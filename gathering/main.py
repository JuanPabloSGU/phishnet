import sys
import os
import csv
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from utils import download_from_url, load_csv_to_es
import logging

ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST')
ELASTICSEARCH_USER = os.getenv('ELASTICSEARCH_USER')
ELASTICSEARCH_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD')

# Malicious URL Feeds
OPENFISH_URL = os.getenv('OPENFISH_URL')
PHISHING_DATABASE_URL = os.getenv('PHISHING_DATABASE_URL')

def malicious_urls(es_client, url, index, stream):
    logging.info(f'Downloading data from {url}')
    data = download_from_url(url, stream)
    if data.status_code != 200:
        return
    
    logging.info(f'Writing data to {index}.csv')
    with open(f'{index}.csv', 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(['url', 'type'])
        row = data.split('\n') + ['1']
        writer.writerows(row)

    logging.info(f'Loading data into Elasticsearch')
    load_csv_to_es(f'{index}.csv', es_client, index)

    logging.info(f'Completed loading {index} into Elasticsearch')

def main():
    logging.basicConfig(level=logging.INFO)
    logging.info('Loading environment variables')
    load_dotenv('.env')

    logging.info('Connecting to Elasticsearch')
    es_client = Elasticsearch(
        ELASTICSEARCH_HOST,
        basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD),
        request_timeout=60
    )

    try:
        info = es_client.info()
        logging.info('Connected to Elasticsearch:', info)
    except Exception as e:
        logging.critical('Could not connect to Elasticsearch:', e)
        sys.exit(1)

    logging.info('Processing malicious URLs for f{OPENFISH_URL}') 
    malicious_urls(es_client, OPENFISH_URL, 'openfish', False)

    logging.info('Processing malicious URLs for f{PHISHING_DATABASE_URL}')
    malicious_urls(es_client, PHISHING_DATABASE_URL, 'phishing_database', True)
    
    logging.info('Completed all tasks.') 

if __name__ == '__main__':
    main()
