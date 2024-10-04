import aiohttp
import asyncio
import logging
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.INFO)

from artint.src.features.Content import Content
from artint.src.features.Domain import Domain
from artint.src.features.Lexical import Lexical
from artint.src.features.DOM import DOM
from artint.src.features.ApiKeyManager import ApiKeyManager
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# Initialize feature extractors that don't require a session
domain_extractor = Domain()
lexical_extractor = Lexical()

load_dotenv('.env')
API_KEY_URLSCAN = os.getenv('URLSCAN_API_KEY')

# Function to initialize Elasticsearch client
def initialize_es_client():
    # Load environment variables from .env file
    logging.info('Loading environment variables')
    load_dotenv('.env')
    ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST')
    ELASTICSEARCH_USER = os.getenv('ELASTICSEARCH_USER')
    ELASTICSEARCH_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD')
    # Connect to Elasticsearch
    logging.info('Connecting to Elasticsearch')
    es_client = Elasticsearch(
        ELASTICSEARCH_HOST,
        basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD),
        request_timeout=60
    )
    return es_client

# Function to get all data from an Elasticsearch index
def get_es_index(es, index):
    try:
        logging.info('Getting all data from Elasticsearch index: %s', index)
        query = {"query": {"match_all": {}}}
        response = es.search(index=index, body=query, scroll='1m', size=5000)
        all_data = response['hits']['hits']
        while len(response['hits']['hits']):
            response = es.scroll(scroll_id=response['_scroll_id'], scroll='1m')
            all_data += response['hits']['hits']
        logging.info('Retrieved %d documents from Elasticsearch index: %s', len(all_data), index)
        return all_data
    finally:
        es.clear_scroll(scroll_id=response['_scroll_id'])

# Function to get all URLs from an Elasticsearch index
def get_all_urls(es, index):
    logging.info('Getting all urls from Elasticsearch index: %s', index)
    query = {"_source": ["url"], "query": {"match_all": {}}}
    response = es.search(index=index, body=query, scroll='1m', size=5000)
    all_urls = [hit['_source']['url'] for hit in response['hits']['hits']]
    while len(response['hits']['hits']):
        response = es.scroll(scroll_id=response['_scroll_id'], scroll='1m')
        all_urls += [hit['_source']['url'] for hit in response['hits']['hits']]
    logging.info('Retrieved %d urls from Elasticsearch index: %s', len(all_urls), index)
    return set(all_urls)

# Function to extract all features from a URL
async def extract_features(url_dicts, session, api_key_manager):
    semaphore = asyncio.Semaphore(20)
    content_extractor = Content(session)
    dom_extractor = DOM(session, api_key_manager)

    async def extract_single_url(url_dict):
        async with semaphore:
            url = url_dict['url'].rstrip('/')
            type = url_dict['type']

            # Asynchronous extractors
            content_task = content_extractor.extract(url)
            dom_task = dom_extractor.extract(url)

            # Synchronous extractors
            domain_task = asyncio.to_thread(domain_extractor.extract(url))
            lexical_task = asyncio.to_thread(lexical_extractor.extract(url))

            content_features, dom_features, domain_features, lexical_features = await asyncio.gather(
                content_task,
                dom_task,
                domain_task,
                lexical_task
            )
            return {'url': url, 'type': type, **content_features, **domain_features, **lexical_features, **dom_features}

    tasks = [extract_single_url(url_dict) for url_dict in url_dicts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [result for result in results if result is not None]

# Function to process a batch of URLs and upload the extracted features to Elasticsearch
async def process_and_upload_batch(url_dicts_batch, es_client, index, batch_number, session, api_key_manager):
    logging.info('Extracting features for batch number: %d', batch_number)
    data = await extract_features(url_dicts_batch, session, api_key_manager)
    actions = [
        {
            '_index': index,
            '_source': doc
        }
        for doc in data
    ]
    
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, bulk, es_client, actions)
    logging.info(f'Processed batch number {batch_number} and uploaded into {index} index')

async def main():
    es_client = initialize_es_client()
    SOURCE_INDEX = os.getenv('SOURCE_INDEX')
    DESTINATION_INDEX = os.getenv('DESTINATION_INDEX')

    # Create the destination index if it does not exist
    if not es_client.indices.exists(index=DESTINATION_INDEX):
        logging.info(f'Index {DESTINATION_INDEX} does not exist. Creating index {DESTINATION_INDEX}')
        es_client.indices.create(index=DESTINATION_INDEX)

    raw_data = get_es_index(es_client, SOURCE_INDEX)

    # Get the unique urls from the SOURCE_INDEX
    unique_urls_source = {doc['_source']['url'] for doc in raw_data}
    logging.info(f'Number of unique URLs in the source index: {len(unique_urls_source)}')

    # Get all urls from the DESTINATION_INDEX
    processed_urls = get_all_urls(es_client, DESTINATION_INDEX)
    logging.info(f'Number of processed URLs in the destination index: {len(processed_urls)}')

    # Get the urls that have not yet been processed along with their type
    unprocessed_url_and_type = {doc['_source']['url']: doc['_source']['type'] 
        for doc in raw_data if doc['_source']['url'] not in processed_urls}
    logging.info(f'Number of unprocessed URLs: {len(unprocessed_url_and_type)}')

    batch_size = 100
    unprocessed_url_and_type_list = [{'url': url, 'type': type} for url, type in unprocessed_url_and_type.items()]

    API_KEYS_URLSCAN = os.getenv('URLSCAN_API_KEY').split(',')
    api_key_manager = ApiKeyManager(API_KEYS_URLSCAN)

    async with aiohttp.ClientSession() as session:
        # Process the unprocessed URLs in batches
        for i in range(0, len(unprocessed_url_and_type_list), batch_size):
            batch = unprocessed_url_and_type_list[i:i+batch_size]
            batch_index = i // batch_size + 1
            try:
                await process_and_upload_batch(batch, es_client, DESTINATION_INDEX, batch_index, session, api_key_manager)
            except Exception as e:
                logging.error(f"Error processing batch {batch_index}: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())