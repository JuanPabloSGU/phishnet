import logging
import os
import pandas as pd
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from artint.src.features.Content import Content
from artint.src.features.Domain import Domain
from artint.src.features.Lexical import Lexical
from gathering.utils import load_csv_to_es

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

def main():
    logging.basicConfig(level=logging.INFO)
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

    if not es_client.indices.exists(index="featext"):
        logging.info(f'Index featext does not exist. Creating index featext')
        es_client.indices.create(index="featext")

    raw_data = get_es_index(es_client, 'raw')

    # Get the urls that have not yet been processed along with their type
    unique_urls = {doc['_source']['url'] for doc in raw_data}
    featext_query = {"query": {"terms": {"url.keyword": list(unique_urls)}}}
    result = es_client.search(index="featext", body=featext_query)
    processed_urls = {hit['_source']['url'] for hit in result['hits']['hits']}
    unprocessed_url_and_type = ({'url': doc['_source']['url'], 'type': doc['_source']['type']} 
                        for doc in raw_data if doc['_source']['url'] not in processed_urls)
    
    logging.info('Extracting features')
    data = extract_features(unprocessed_url_and_type)

    logging.info('Saving features to features.csv')
    df = pd.DataFrame(data)
    df.to_csv('features.csv', index=False)

    load_csv_to_es('features.csv', es_client, 'featext')

if __name__ == "__main__":
    main()