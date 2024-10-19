import aiohttp
import asyncio
import hashlib
import logging
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.INFO)

import utilities.ServiceUtils as ServiceUtils
from artint.src.features.Content import Content
from artint.src.features.Domain import Domain
from artint.src.features.Lexical import Lexical
from artint.src.features.DOM import DOM
from artint.src.features.ApiKeyManager import ApiKeyManager
from dotenv import load_dotenv
from elasticsearch.helpers import bulk, BulkIndexError

feature_extractors = ['Content', 'Domain', 'Lexical', 'DOM']
successes = {extractor: 0 for extractor in feature_extractors}
failures = {extractor: 0 for extractor in feature_extractors}

# Function to extract all features from a URL
async def extract_single_url(doc, processed_ids, semaphore, session, api_key_manager):
    async with semaphore:
        url = doc['url'].rstrip('/')
        type = doc['type']

        url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()

        if url_hash in processed_ids:
            return None  # Skip processing this URL

        domain_extractor = Domain()
        lexical_extractor = Lexical()
        content_extractor = Content(session)
        dom_extractor = DOM(session, api_key_manager)

        # Asynchronous extractors
        content_task = content_extractor.extract(url)
        dom_task = dom_extractor.extract(url)

        # Synchronous extractors
        domain_task = asyncio.to_thread(domain_extractor.extract, url)
        lexical_task = asyncio.to_thread(lexical_extractor.extract, url)

        content_features, dom_features, domain_features, lexical_features = await asyncio.gather(
            content_task,
            dom_task,
            domain_task,
            lexical_task
        )

        feature_dicts = {
            'Content': content_features,
            'DOM': dom_features,
            'Domain': domain_features,
            'Lexical': lexical_features
        }

        for extractor_name, features in feature_dicts.items():
            if ServiceUtils.check_failure(features):
                failures[extractor_name] += 1
            else:
                successes[extractor_name] += 1

        return {
            '_id': url_hash,
            '_source': {
                'url': url,
                'type': type,
                **content_features,
                **domain_features,
                **lexical_features,
                **dom_features
            }
        }

# Function to extract features from a batch of URLs
async def extract_features(docs_batch, processed_ids, session, api_key_manager):
    semaphore = asyncio.Semaphore(180)

    tasks = [
        extract_single_url(doc, processed_ids, semaphore, session, api_key_manager)
        for doc in docs_batch
    ]
    results = await asyncio.gather(*tasks)
    valid_results = [result for result in results if result is not None]
    return valid_results

# Function to process a batch of URLs and upload the extracted features to Elasticsearch
async def process_and_upload_batch(docs_batch, es_client, index, batch_number, session, api_key_manager, processed_ids):
    logging.info(f'\nExtracting features for batch number: {batch_number}\n')
    docs_batch = ServiceUtils.deduplicate_batch(docs_batch)

    data = await extract_features(docs_batch, processed_ids, session, api_key_manager)
    data = [doc for doc in data if doc is not None]
    if not data:
        logging.info(f"\nNo new documents to index for batch {batch_number}.\n")
        return

    actions = [
        {
            '_index': index,
            '_id': doc['_id'],
            '_source': doc['_source']
        }
        for doc in data
    ]
    
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, bulk, es_client, actions)
        logging.info(f'\nProcessed batch number {batch_number} and uploaded into {index} index\n')
    except BulkIndexError as e:
        logging.error(f"Bulk indexing failed for batch {batch_number}")
        for error in e.errors:
            logging.error(f"Failed to index document: {error}")

    # Update processed_ids with the IDs just processed
    processed_ids.update([doc['_id'] for doc in data])

    # Log batch summary
    batch_summary = f"Total summary after Batch {batch_number}:\n"
    for extractor in feature_extractors:
        batch_summary += f"{extractor} - Total Successes: {successes[extractor]}, Total Failures: {failures[extractor]}\n"
    logging.info(batch_summary)

async def main():
    load_dotenv(override=True)
    
    # Get environment variables
    ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST')
    ELASTICSEARCH_USER = os.getenv('ELASTICSEARCH_USER')
    ELASTICSEARCH_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD')
    SOURCE_INDEX = os.getenv('SOURCE_INDEX')
    DESTINATION_INDEX = os.getenv('DESTINATION_INDEX')
    API_KEYS_URLSCAN = os.getenv('URLSCAN_API_KEY').split(',')

    es_client = ServiceUtils.initialize_es_client(ELASTICSEARCH_HOST, ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD)
    # Create the destination index if it does not exist
    if not es_client.indices.exists(index=DESTINATION_INDEX):
        logging.info(f'Index {DESTINATION_INDEX} does not exist. Creating index {DESTINATION_INDEX}')
        es_client.indices.create(index=DESTINATION_INDEX)

    raw_data = ServiceUtils.get_es_index(es_client, SOURCE_INDEX)

    # Extract url and type from raw_data
    source_docs = [
        {'url': doc['_source']['url'], 'type': doc['_source']['type']}
        for doc in raw_data
    ]
    logging.info(f'Number of documents in the source index: {len(source_docs)}')

    # Get all ids from the destination index
    processed_ids = ServiceUtils.get_all_ids(es_client, DESTINATION_INDEX)
    logging.info(f'Number of processed IDs in the destination index: {len(processed_ids)}')

    batch_size = 300
    api_key_manager = ApiKeyManager(API_KEYS_URLSCAN)

    async with aiohttp.ClientSession() as session:
        # Process the unprocessed URLs in batches
        for i in range(0, len(source_docs), batch_size):
            batch = source_docs[i:i+batch_size]
            batch_index = i // batch_size + 1
            try:
                await process_and_upload_batch(batch, es_client, DESTINATION_INDEX, batch_index, session, api_key_manager, processed_ids)
            except Exception as e:
                logging.error(f"Error processing batch {batch_index}: {e}", exc_info=True)
        
        final_summary = "Final Summary:\n"
        for extractor in feature_extractors:
            final_summary += f"{extractor} - Total Successes: {successes[extractor]}, Total Failures: {failures[extractor]}\n"
        logging.info(final_summary)

if __name__ == "__main__":
    asyncio.run(main())