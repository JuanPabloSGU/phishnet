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
def extract_features(url):
    features = {}
    for feature_class in [Content, Domain, Lexical]:
        feature_extractor = feature_class([url])
        feature_extractor.extract()
        features.update(feature_extractor.feat_dict)
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

    raw_data = get_es_index(es_client, 'raw')
    data = []
    logging.info('Extracting features from raw data')
    for doc in raw_data:
        url = doc['_source']['url']
        type = doc['_source']['type']
        features = extract_features(url)
        data.append({'url': url, 'type': type, **features})

    logging.info('Saving features to features.csv')
    df = pd.DataFrame(data)
    df.to_csv('features.csv', index=False)

    load_csv_to_es('features.csv', es_client, 'featext')

if __name__ == "__main__":
    main()