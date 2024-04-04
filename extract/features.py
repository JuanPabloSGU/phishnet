import concurrent.futures
import logging
import os
import pandas as pd
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.INFO)

from artint.src.features.Content import Content
from artint.src.features.Domain import Domain
from artint.src.features.Lexical import Lexical
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from gathering.utils import load_csv_to_es, add_protocol

content_extractor = Content()
domain_extractor = Domain()
lexical_extractor = Lexical()

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
def extract_features(url_dicts):
    features = []
    for url_dict in url_dicts:
        url = add_protocol(url_dict['url'])
        if url is None:
            continue
        type = url_dict['type']
        content_features = content_extractor.extract(url)
        domain_features = domain_extractor.extract(url)
        lexical_features = lexical_extractor.extract(url)
        features.append({'url': url, 'type': type, **content_features, **domain_features, **lexical_features})
    return features


def process_and_upload_batch(url_dicts_batch, index, batch_number):
    es_client = initialize_es_client()

    logging.info('Extracting features')
    data = extract_features(url_dicts_batch)

    csv_file = f'features_{batch_number}.csv'
    logging.info(f'Saving features to {csv_file}')
    df = pd.DataFrame(data)
    df.to_csv(csv_file, index=False)

    load_csv_to_es(csv_file, es_client, index)
    logging.info(f'Processed batch number {batch_number} and uploaded into {index} index')

    os.remove(csv_file) # Delete CSV file after loading it into Elasticsearch

def main():
    es_client = initialize_es_client()
    SOURCE_INDEX = os.getenv('SOURCE_INDEX')
    DESTINATION_INDEX = os.getenv('DESTINATION_INDEX')

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

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for i in range(0, len(unprocessed_url_and_type_list), batch_size):
            batch = unprocessed_url_and_type_list[i:i+batch_size]

            future = executor.submit(process_and_upload_batch, batch)

            batch_index = i // batch_size + 1
            future = executor.submit(process_and_upload_batch, batch, DESTINATION_INDEX, batch_index)

            futures.append(future)

    # Wait for all processes to complete
    for future in concurrent.futures.as_completed(futures):
        if future.exception() is not None:
            logging.error(f"Error in thread: {future.exception()}")

if __name__ == "__main__":
    main()