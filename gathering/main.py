import csv
import logging
import os
import sys
import utils
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

def fetch_and_index_urls(es_client, source, index, stream, type, is_url):
    if is_url:
        logging.info(f'Downloading data from {source}')
        data = utils.download_from_url(source, stream)
        if data.status_code != 200:
            return
        urls = data.iter_lines()
    else:
        logging.info(f'Reading data from {source}')
        try:
            with open(source, 'r') as file:
                urls = file.readlines()
        except Exception as e:
            logging.error(f'Error reading file {source}: {e}')
            return

    if not es_client.indices.exists(index=index):
        logging.info(f'Index {index} does not exist. Creating index {index}')
        es_client.indices.create(index=index)

    logging.info(f'Writing data to {index}.csv')
    with open(f'{index}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['url', 'type'])
        for row in urls:
            url = row.decode() if is_url else row.strip()
            url = utils.add_protocol(url)
            if url is None:
                continue

            # Check if the URL is already in Elasticsearch
            res = es_client.search(index=index, body={
                'query': {
                    'term': {
                        'url.keyword': url
                    }
                }
            })

            # If the URL is already in Elasticsearch, skip it
            if res['hits']['total']['value'] > 0:
                logging.info(f'{url} already exists in {index}')
                continue

            writer.writerow([url, type])

    logging.info(f'Loading data into Elasticsearch')
    utils.load_csv_to_es(f'{index}.csv', es_client, index)

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

    # One time use in case the database is cleared and we need to re-import the data
    # logging.info("Loading 'PhiUSIIL url and type.csv' into Elasticsearch, skipping search due to empty index.")
    # utils.load_csv_to_es('backups/PhiUSIIL url and type.csv', es_client, 'raw')
    # logging.info("Processing malicious URLs for 'openphish.txt'")
    # fetch_and_index_urls(es_client, 'backups/openphish.txt', 'raw', False, 1, False)
    logging.info("Processing benign URLs for 'benign-top-1000000-1.txt'")
    fetch_and_index_urls(es_client, 'backups/benign-top-1000000-1.txt', 'raw', False, 0, False)

    logging.info('Processing malicious URLs for f{OPENFISH_URL}') 
    fetch_and_index_urls(es_client, OPENFISH_URL, 'raw', False, 1, True)

    logging.info('Processing malicious URLs for f{PHISHING_DATABASE_URL}')
    fetch_and_index_urls(es_client, PHISHING_DATABASE_URL, 'raw', True, 1, True)

    logging.info('Completed all tasks.') 

if __name__ == '__main__':
    main()
