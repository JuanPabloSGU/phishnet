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
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from gathering.utils import preprocess_url

# Initialize feature extractors
content_extractor = Content()
domain_extractor = Domain()
lexical_extractor = Lexical()

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
async def extract_features(session, url_dicts):
    semaphore = asyncio.Semaphore(100)

    async def extract_single_url(url_dict):
        async with semaphore:
            url = await preprocess_url(session, url_dict['url'])
            if url is None:
                return None
            logging.info('URL: %s is valid', url)
            type = url_dict['type']
            content_features = await content_extractor.extract(url)
            domain_features = domain_extractor.extract(url)
            lexical_features = lexical_extractor.extract(url)
            return {'url': url, 'type': type, **content_features, **domain_features, **lexical_features}

    tasks = [extract_single_url(url_dict) for url_dict in url_dicts]
    results = await asyncio.gather(*tasks)
    return [result for result in results if result is not None]

# Function to process a batch of URLs and upload the extracted features to Elasticsearch
async def process_and_upload_batch(session, url_dicts_batch, es_client, index, batch_number):
    logging.info('Extracting features for batch number: %d', batch_number)
    data = await extract_features(session, url_dicts_batch)
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

    batch_size = 1000
    futures = []
    unprocessed_url_and_type_list = [{'url': url, 'type': type} for url, type in unprocessed_url_and_type.items()]

    async with aiohttp.ClientSession() as session:
        # Process the unprocessed URLs in batches
        for i in range(0, len(unprocessed_url_and_type_list), batch_size):
            batch = unprocessed_url_and_type_list[i:i+batch_size]
            batch_index = i // batch_size + 1
            task = asyncio.create_task(
                process_and_upload_batch(session, batch, es_client, DESTINATION_INDEX, batch_index)
            )
            futures.append(task)

        for future in asyncio.as_completed(futures):
            try:
                await future
            except Exception as e:
                logging.error(f"Error in task: {e}")

if __name__ == "__main__":
    asyncio.run(main())