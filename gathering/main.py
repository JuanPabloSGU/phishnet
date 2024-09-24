import asyncio
import aiohttp
import hashlib
import logging
import os
import sys
import utils
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers
from asyncio import Semaphore, Lock

# Function to fetch and index urls
async def fetch_and_index_urls(es_client, session, source, index, stream, type, is_url):
    # Initialize a semaphore to limit the number of concurrent tasks to 50
    semaphore = Semaphore(50)
    batch_size = 1000
    actions_lock = Lock()
    actions = []

    if is_url: # If the source is a URL
        logging.info(f'Downloading data from {source}')
        data = utils.download_from_url(source, stream)
        if data is None:
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
    async def process_url(row):
        async with semaphore:
            url = row.decode() if is_url else row.strip()
            url = await utils.preprocess_url(session, url)
            if url is None:
                return

            url_id = hashlib.sha256(url.encode('utf-8')).hexdigest()
            action = {
                '_index': index,
                '_id': url_id,
                '_source': {
                    'url': url,
                    'type': type
                }
            }

            async with actions_lock:
                actions.append(action)
                if len(actions) >= batch_size:
                    await asyncio.to_thread(helpers.bulk, es_client, actions)
                    actions.clear()

    tasks = [process_url(row) for row in urls]
    await asyncio.gather(*tasks)

    async with actions_lock:
        if actions:
            await asyncio.to_thread(helpers.bulk, es_client, actions)
            actions.clear()

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

    TARGET_INDEX = 'raw'

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
        logging.info(f'Connected to Elasticsearch: {info}')
    except Exception as e:
        logging.critical(f'Could not connect to Elasticsearch: {e}')
        sys.exit(1)

    async with aiohttp.ClientSession() as session:
        # If BACKUP is set to 'True', create a raw index and load data into it
        BACKUP = os.getenv('BACKUP')
        if BACKUP == 'True':
            if not es_client.indices.exists(index=TARGET_INDEX):
                es_client.indices.create(index=TARGET_INDEX)

            # One time use in case the database is cleared and we need to re-import the data
            logging.info("Loading 'PhiUSIIL - benign.txt' into Elasticsearch, skipping search due to empty index.")
            await fetch_and_index_urls(es_client, session, 'backups/PhiUSIIL - benign.txt', TARGET_INDEX, False, 0, False)
            
            logging.info("Processing benign URLs for 'PhiUSIIL - malicious.txt'")
            await fetch_and_index_urls(es_client, session, 'backups/PhiUSIIL - malicious.txt', TARGET_INDEX, False, 1, False)

            logging.info("Processing benign URLs for 'benign-top-1000000-1.txt'")
            await fetch_and_index_urls(es_client, session, 'backups/benign-top-1000000-1.txt', TARGET_INDEX, False, 0, False)

            logging.info("Processing benign URLs for 'mendeley benign - Webpages_Classification_test_data-1.txt'")
            await fetch_and_index_urls(es_client, session, 'backups/mendeley benign - Webpages_Classification_test_data-1.txt', TARGET_INDEX, False, 0, False)

            logging.info("Processing malicious URLs for 'openphish.txt'")
            await fetch_and_index_urls(es_client, session, 'backups/openphish.txt', TARGET_INDEX, False, 1, False)

        # Process malicious URLs from OpenFish and Phishing Database
        logging.info(f'Processing malicious URLs for {OPENFISH_URL}') 
        await fetch_and_index_urls(es_client, session, OPENFISH_URL, TARGET_INDEX, False, 1, True)

        logging.info(f'Processing malicious URLs for {PHISHING_DATABASE_URL}')
        await fetch_and_index_urls(es_client, session, PHISHING_DATABASE_URL, TARGET_INDEX, True, 1, True)

    logging.info('Completed all tasks.')

if __name__ == '__main__':
    asyncio.run(main())
