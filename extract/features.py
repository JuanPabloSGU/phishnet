import aiohttp
import asyncio
import hashlib
import logging
import os
import sys

# Add the parent directory to the system path to import utility modules
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

# List of feature extractors to be used
feature_extractors = ['Content', 'Domain', 'Lexical', 'DOM']

# Initialize dictionaries to keep track of successes and failures for each extractor
successes = {extractor: 0 for extractor in feature_extractors}
failures = {extractor: 0 for extractor in feature_extractors}

# Function to extract all features from a URL
async def extract_single_url(doc, processed_ids, semaphore, session, api_key_manager):
    """
    Extracts features from a single URL document and returns the processed document.

    This function checks if the URL has already been processed. If not, it uses various
    feature extractors to extract features from the URL and compiles them into a document
    suitable for indexing into Elasticsearch.

    Parameters:
    doc (dict): A dictionary containing the 'url' and its 'type' (e.g., 0 for benign or 1 for malicious).
    processed_ids (set): A set of URL hashes that have already been processed.
    semaphore (asyncio.Semaphore): Semaphore to limit concurrent processing.
    session (aiohttp.ClientSession): The aiohttp session used for HTTP requests.
    api_key_manager (ApiKeyManager): Manages URLScan API keys to be used within the DOM feature extractor.

    Returns:
    dict or None: A dictionary representing the processed document with extracted features,
                  or None if the URL has already been processed.
    """
    async with semaphore:
        # Extract URL and its type from the document
        url = doc['url'].rstrip('/')
        type = doc['type']

        # Generate a SHA-256 hash of the URL to use as a unique identifier (preventing duplicates)
        url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()

        # Skip processing if the URL has already been processed
        if url_hash in processed_ids:
            return None

        # Initialize feature extractors
        domain_extractor = Domain()
        lexical_extractor = Lexical()
        content_extractor = Content(session)
        dom_extractor = DOM(session, api_key_manager)

        # Initiate asynchronous feature extraction tasks
        content_task = content_extractor.extract(url)
        dom_task = dom_extractor.extract(url)

        # Initiate synchronous feature extraction tasks in separate threads
        domain_task = asyncio.to_thread(domain_extractor.extract, url)
        lexical_task = asyncio.to_thread(lexical_extractor.extract, url)

        # Await the completion of all feature extraction tasks
        content_features, dom_features, domain_features, lexical_features = await asyncio.gather(
            content_task,
            dom_task,
            domain_task,
            lexical_task
        )

        # Compile all extracted features into a dictionary
        feature_dicts = {
            'Content': content_features,
            'DOM': dom_features,
            'Domain': domain_features,
            'Lexical': lexical_features
        }

        # Update success and failure counts based on feature extraction results
        for extractor_name, features in feature_dicts.items():
            if ServiceUtils.check_failure(features):
                failures[extractor_name] += 1
            else:
                successes[extractor_name] += 1

        # Construct the document to be indexed into Elasticsearch
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

async def extract_features(docs_batch, processed_ids, session, api_key_manager):
    """
    Extracts features from a batch of URL documents.

    This function concurrently processes a batch of URLs, extracting features from each
    using the `extract_single_url` function.

    Parameters:
    docs_batch (list): A list of document dictionaries containing URLs and their types.
    processed_ids (set): A set of URL hashes that have already been processed.
    session (aiohttp.ClientSession): The aiohttp session used for HTTP requests.
    api_key_manager (ApiKeyManager): Manages URLScan API keys to be used within the DOM feature extractor.

    Returns:
    list: A list of processed documents with extracted features.
    """
    # Define a semaphore to limit the number of concurrent feature extraction tasks
    semaphore = asyncio.Semaphore(180)

    # Create a list of tasks for feature extraction
    tasks = [
        extract_single_url(doc, processed_ids, semaphore, session, api_key_manager)
        for doc in docs_batch
    ]

    # Execute all tasks concurrently, filter out any None results (URLs that were already processed)
    results = await asyncio.gather(*tasks)
    valid_results = [result for result in results if result is not None]
    return valid_results

# Function to process a batch of URLs and upload the extracted features to Elasticsearch
async def process_and_upload_batch(docs_batch, es_client, index, batch_number, session, api_key_manager, processed_ids):
    """
    Processes a batch of URLs by extracting features and uploading the results to Elasticsearch.

    This function deduplicates the batch, extracts features from each URL, and then uploads
    the processed documents to the specified Elasticsearch index using bulk indexing.

    Parameters:
    docs_batch (list): A list of document dictionaries containing URLs and their types.
    es_client (Elasticsearch): The Elasticsearch client instance.
    index (str): The name of the Elasticsearch index to upload documents to.
    batch_number (int): The sequential number of the current batch being processed.
    session (aiohttp.ClientSession): The aiohttp session used for HTTP requests.
    api_key_manager (ApiKeyManager): Manages URLScan API keys to be used within the DOM feature extractor.
    processed_ids (set): A set of URL hashes that have already been processed.

    Returns:
    None
    """
    logging.info(f'\nExtracting features for batch number: {batch_number}\n')

    # Deduplicate the batch to remove any duplicate URLs
    docs_batch = ServiceUtils.deduplicate_batch(docs_batch)

    # Extract features from the deduplicated batch, filter out any None results
    data = await extract_features(docs_batch, processed_ids, session, api_key_manager)
    data = [doc for doc in data if doc is not None]
    if not data:
        logging.info(f"\nNo new documents to index for batch {batch_number}.\n")
        return

    # Prepare actions for bulk indexing into Elasticsearch
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
        # Perform bulk indexing in a separate thread to avoid blocking the event loop
        await loop.run_in_executor(None, bulk, es_client, actions)
        logging.info(f'\nProcessed batch number {batch_number} and uploaded into {index} index\n')
    except BulkIndexError as e:
        logging.error(f"Bulk indexing failed for batch {batch_number}")
        for error in e.errors:
            logging.error(f"Failed to index document: {error}")

    # Update the set of processed IDs with the newly indexed documents
    processed_ids.update([doc['_id'] for doc in data])

    # Log a summary: Running total of successes and failures after the current batch
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

    # Retrieve all documents from the source Elasticsearch index
    raw_data = ServiceUtils.get_es_index(es_client, SOURCE_INDEX)

    # Extract 'url' and 'type' from each document in the raw data
    source_docs = [
        {'url': doc['_source']['url'], 'type': doc['_source']['type']}
        for doc in raw_data
    ]
    logging.info(f'Number of documents in the source index: {len(source_docs)}')

    # Retrieve all processed URL IDs from the destination index to avoid reprocessing
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
        
        # Compile and log a final summary of all successes and failures
        final_summary = "Final Summary:\n"
        for extractor in feature_extractors:
            final_summary += f"{extractor} - Total Successes: {successes[extractor]}, Total Failures: {failures[extractor]}\n"
        logging.info(final_summary)

if __name__ == "__main__":
    asyncio.run(main())