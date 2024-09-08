import asyncio
import aiohttp
import csv
import logging
import os
import sys
import utils
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

session = aiohttp.ClientSession()

# Function to fetch and index urls
async def fetch_and_index_urls(es_client, source, index, stream, type, is_url):
    if is_url: # If the source is a URL
        logging.info(f'Downloading data from {source}')
        data = utils.download_from_url(source, stream)
        if data.status_code != 200:
            return
        urls = data.iter_lines()
    else: # If the source is a file
        logging.info(f'Reading data from {source}')
        try:
            with open(source, 'r') as file:
                urls = file.readlines()
        except Exception as e:
            logging.error(f'Error reading file {source}: {e}')
            return

    # If the index does not exist in Elasticsearch, create it
    if not es_client.indices.exists(index=index):
        logging.info(f'Index {index} does not exist. Creating index {index}')
        es_client.indices.create(index=index)

    # Write the URLs along with their type to a CSV file
    # A type of 0 is benign and a type of 1 is malicious
    logging.info(f'Writing data to {index}.csv')
    with open(f'{index}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['url', 'type'])

        async def process_url(row):
            url = row.decode() if is_url else row.strip()
            url = await utils.add_protocol(session, url)
            if url is None:
                return None

            res = es_client.search(index=index, body={
                'query': {
                    'term': {
                        'url.keyword': url
                    }
                }
            })

            if res['hits']['total']['value'] > 0:
                logging.info(f'{url} already exists in {index}')
                return None

            return [url, type]

        tasks = [process_url(row) for row in urls]
        results = await asyncio.gather(*tasks)
        for result in results:
            if result is not None:
                writer.writerow(result)

    logging.info(f'Loading data into Elasticsearch')
    utils.load_csv_to_es(f'{index}.csv', es_client, index)

    logging.info(f'Completed loading {index} into Elasticsearch')

async def main():
    logging.basicConfig(level=logging.INFO)
    logging.info('Loading environment variables')
    load_dotenv(override=True)

    # Get environment variables
    ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST')
    ELASTICSEARCH_USER = os.getenv('ELASTICSEARCH_USER')
    ELASTICSEARCH_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD')
    OPENFISH_URL = os.getenv('OPENFISH_URL')
    PHISHING_DATABASE_URL = os.getenv('PHISHING_DATABASE_URL')

    # Connect to Elasticsearch
    logging.info('Connecting to Elasticsearch')
    es_client = Elasticsearch(
        ELASTICSEARCH_HOST,
        basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD),
        request_timeout=60
    )

    # Test the Elasticsearch connection
    logging.info('Testing Elasticsearch connection')
    try:
        info = es_client.info()
        logging.info('Connected to Elasticsearch:', info)
    except Exception as e:
        logging.critical('Could not connect to Elasticsearch:', e)
        sys.exit(1)

    # If BACKUP is set to 'True', create a raw index and load data into it
    BACKUP = os.getenv('BACKUP')
    if BACKUP == 'True':
        es_client.indices.create(index='raw')

        # One time use in case the database is cleared and we need to re-import the data
        logging.info("Loading 'PhiUSIIL url and type.csv' into Elasticsearch, skipping search due to empty index.")
        utils.load_csv_to_es('backups/PhiUSIIL url and type.csv', es_client, 'raw')

        logging.info("Processing benign URLs for 'mendeley benign - Webpages_Classification_test_data-1.txt'")
        await fetch_and_index_urls(es_client, 'backups/mendeley benign - Webpages_Classification_test_data-1.txt', 'raw', False, 0, False)

        logging.info("Processing malicious URLs for 'openphish.txt'")
        await fetch_and_index_urls(es_client, 'backups/openphish.txt', 'raw', False, 1, False)

        logging.info("Processing benign URLs for 'benign-top-1000000-1.txt'")
        await fetch_and_index_urls(es_client, 'backups/benign-top-1000000-1.txt', 'raw', False, 0, False)

    # Process malicious URLs from OpenFish and Phishing Database
    logging.info('Processing malicious URLs for f{OPENFISH_URL}') 
    await fetch_and_index_urls(es_client, OPENFISH_URL, 'raw', False, 1, True)

    logging.info('Processing malicious URLs for f{PHISHING_DATABASE_URL}')
    await fetch_and_index_urls(es_client, PHISHING_DATABASE_URL, 'raw', True, 1, True)
        
    logging.info('Completed all tasks.') 
    await session.close()

if __name__ == '__main__':
    asyncio.run(main())
