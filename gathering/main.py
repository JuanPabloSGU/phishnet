import sys
import os
import csv
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from utils import download_from_url, load_csv_to_es
import logging


def malicious_urls(es_client, url, index, stream):
    logging.info(f'Downloading data from {url}')
    data = download_from_url(url, stream)
    if data.status_code != 200:
        return

    if not es_client.indices.exists(index=index):
        logging.info(f'Index {index} does not exist. Creating index {index}')
        es_client.indices.create(index=index)
    
    logging.info(f'Writing data to {index}.csv')
    with open(f'{index}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['url', 'type'])
        for row in data.iter_lines():
            url = row.decode()

            # Check if the URL is already in elasticsearch
            res = es_client.search(index=index, body={
                'query': {
                    'term': {
                        'url.keyword': url
                    }
                }
            })

            # If the URL is already in Elasticsearch, skip it
            if res['hits']['total']['value'] == 0:
                logging.info(f'{url} already exists in {index}')
                continue

            writer.writerow([url, '1'])

    logging.info(f'Loading data into Elasticsearch')
    load_csv_to_es(f'{index}.csv', es_client, index)

    logging.info(f'Completed loading {index} into Elasticsearch')

def malicious_urls_from_file(es_client, file_path, index):
    logging.info(f'Reading data from {file_path}')
    try:
        with open(file_path, 'r') as file:
            urls = file.readlines()
    except Exception as e:
        logging.error(f'Error reading file {file_path}: {e}')
        return

    if not es_client.indices.exists(index=index):
        logging.info(f'Index {index} does not exist. Creating index {index}')
        es_client.indices.create(index=index)

    logging.info(f'Writing data to {index}.csv')
    with open(f'{index}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['url', 'type'])
        for url in urls:
            url = url.strip()

            # Check if the URL is already in Elasticsearch
            res = es_client.search(index=index, body={
                'query': {
                    'term': {
                        'url.keyword': url
                    }
                }
            })

            # If the URL is already in Elasticsearch, skip it
            if res['hits']['total']['value'] == 0:
                logging.info(f'{url} already exists in {index}')
                continue

            writer.writerow([url, '1'])

    logging.info(f'Loading data into Elasticsearch')
    load_csv_to_es(f'{index}.csv', es_client, index)

    logging.info(f'Completed loading {index} into Elasticsearch')


def main():
    logging.basicConfig(level=logging.INFO)
    logging.info('Loading environment variables')
    load_dotenv(override=True)

    ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST')
    ELASTICSEARCH_USER = os.getenv('ELASTICSEARCH_USER')
    ELASTICSEARCH_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD')
    OPENFISH_URL = os.getenv('OPENFISH_URL')
    PHISHING_DATABASE_URL = os.getenv('PHISHING_DATABASE_URL')

    logging.info('Connecting to Elasticsearch')
    es_client = Elasticsearch(
        ELASTICSEARCH_HOST,
        basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD),
        request_timeout=60
    )

    logging.info('Testing Elasticsearch connection')

    try:
        info = es_client.info()
        logging.info('Connected to Elasticsearch:', info)
    except Exception as e:
        logging.critical('Could not connect to Elasticsearch:', e)
        sys.exit(1)

    logging.info('Processing malicious URLs for f{OPENFISH_URL}') 
    malicious_urls(es_client, OPENFISH_URL, 'raw', False)

    logging.info('Processing malicious URLs for f{PHISHING_DATABASE_URL}')
    malicious_urls(es_client, PHISHING_DATABASE_URL, 'raw', True)

    # One time use in case the database is cleared and we need to re-import the data
    # logging.info('Processing malicious URLs for backup.txt')
    # malicious_urls_from_file(es_client, 'backup.txt', 'raw')
    
    logging.info('Completed all tasks.') 

if __name__ == '__main__':
    main()
