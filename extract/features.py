import concurrent.futures
import logging
import os
import pandas as pd
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from artint.src.features.Content import Content
from artint.src.features.Domain import Domain
from artint.src.features.Lexical import Lexical
from gathering.utils import load_csv_to_es

def initialize_es_client():
    logging.info('Loading environment variables')
    load_dotenv('.env')
    ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST')
    ELASTICSEARCH_USER = os.getenv('ELASTICSEARCH_USER')
    ELASTICSEARCH_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD')

    logging.info('Connecting to Elasticsearch')
    es_client = Elasticsearch(
        ELASTICSEARCH_HOST,
        basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD),
        request_timeout=60
    )
    return es_client

# Function to get all data from an Elasticsearch index
def get_es_index(es, index):
    logging.info('Getting all data from Elasticsearch index: %s', index)
    query = {"query": {"match_all": {}}}
    response = es.search(index=index, body=query, scroll='1m', size=5000)
    all_data = response['hits']['hits']
    while len(response['hits']['hits']):
        response = es.scroll(scroll_id=response['_scroll_id'], scroll='1m')
        all_data += response['hits']['hits']
    logging.info('Retrieved %d documents from Elasticsearch index: %s', len(all_data), index)
    return all_data

def chunked_search(es, index, urls, chunk_size=1000):
    for i in range(0, len(urls), chunk_size):
        chunk = urls[i:i+chunk_size]
        query = {"query": {"terms": {"url.keyword": chunk}}}
        yield from es.search(index=index, body=query, size=len(chunk))['hits']['hits']

# Function to extract all features from a URL
def extract_features(url_dicts):
    content_extractor = Content()
    domain_extractor = Domain()
    lexical_extractor = Lexical()
    features = []
    for url_dict in url_dicts:
        url = url_dict['url']
        type = url_dict['type']
        content_features = content_extractor.extract(url)
        domain_features = domain_extractor.extract(url)
        lexical_features = lexical_extractor.extract(url)
        features.append({'url': url, 'type': type, **content_features, **domain_features, **lexical_features})
    return features

def process_and_upload_batch(url_dicts_batch):
    es_client = initialize_es_client()

    logging.info('Extracting features')
    data = extract_features(url_dicts_batch)

    logging.info('Saving features to features.csv')
    df = pd.DataFrame(data)
    df.to_csv('features.csv', index=False)

    load_csv_to_es('features.csv', es_client, 'featext')

def main():
    es_client = initialize_es_client()

    if not es_client.indices.exists(index="featext"):
        logging.info(f'Index featext does not exist. Creating index featext')
        es_client.indices.create(index="featext")

    raw_data = get_es_index(es_client, 'raw')

    # Get the urls that have not yet been processed along with their type
    unique_urls = {doc['_source']['url'] for doc in raw_data}
    processed_urls = set()
    for hit in chunked_search(es_client, "featext", list(unique_urls)):
        processed_urls.add(hit['_source']['url'])
    unprocessed_url_and_type = [{'url': doc['_source']['url'], 'type': doc['_source']['type']} 
                        for doc in raw_data if doc['_source']['url'] not in processed_urls]
    logging.info(f'Number of unprocessed URLs: {len(unprocessed_url_and_type)}')

    batch_size = 1000
    futures = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for i in range(0, len(unprocessed_url_and_type), batch_size):
            batch = unprocessed_url_and_type[i:i+batch_size]
            future = executor.submit(process_and_upload_batch, batch)
            futures.append(future)

    # Wait for all processes to complete
    completed_tasks = 0
    for future in concurrent.futures.as_completed(futures):
        if future.exception() is not None:
            logging.error(f"Error in thread: {future.exception()}")
        else:
            completed_tasks += batch_size
            logging.info(f'Processed {completed_tasks} out of {len(unprocessed_url_and_type)} URLs')

if __name__ == "__main__":
    main()