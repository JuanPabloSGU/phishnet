import asyncio
import aiohttp
import hashlib
import logging
import os
import sys

# Add the parent directory to the system path to import utilities
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utilities.ServiceUtils as ServiceUtils
from dotenv import load_dotenv
from elasticsearch import helpers
from asyncio import Semaphore, Lock

# Function to fetch and index urls
async def fetch_and_index_urls(es_client, session, source, index, stream, type, is_url):
    '''
    Fetches URLs from a source (either a URL or a file), processes them, and indexes them into Elasticsearch.

    Parameters:
    es_client: Elasticsearch client instance used to interact with the Elasticsearch cluster.
    session: aiohttp.ClientSession instance used for making asynchronous HTTP requests.
    source: The source from which URLs are fetched. It can be a URL or a file path.
    index: The name of the Elasticsearch index where the URLs will be stored.
    stream: Boolean indicating whether the source is a stream.
    type: The type of URLs being processed (e.g., 0 for benign or 1 for malicious).
    is_url: Boolean indicating whether the source is a URL (True) or a file (False).
    '''
    semaphore = Semaphore(100) # Initialize a semaphore to limit the number of concurrent tasks to 100
    batch_size = 1000 # Define the batch size for bulk indexing
    actions_lock = Lock() # Lock to manage access to the actions list
    actions = [] # List to hold bulk indexing actions

    if is_url: # If the source is a URL, download the data
        logging.info(f'Downloading data from {source}')
        data = ServiceUtils.download_from_url(source, stream)
        if data is None:
            return
        # Assume data is a stream of lines
        urls = data.iter_lines()
    else: # If the source is a file, read URLs from the file
        logging.info(f'Reading data from {source}')
        try:
            with open(source, 'r') as file:
                urls = file.readlines()
        except Exception as e:
            logging.error(f'Error reading file {source}: {e}')
            return

    # Check if the Elasticsearch index exists; if not, create it
    if not es_client.indices.exists(index=index):
        logging.info(f'Index {index} does not exist. Creating index {index}')
        es_client.indices.create(index=index)

    # Process each URL
    async def process_url(row):
        async with semaphore:
            url = row.decode() if is_url else row.strip()
            # Preprocess the URL (validation and normalization)
            url = await ServiceUtils.preprocess_url(session, url)
            if url is None:
                return

            # Generate a unique ID for the URL using SHA-256 hashing, preventing duplicates
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
                # If the batch size is reached, perform bulk indexing
                if len(actions) >= batch_size:
                    await asyncio.to_thread(helpers.bulk, es_client, actions)
                    actions.clear()

    # Create a list of tasks for processing all URLs concurrently
    tasks = [process_url(row) for row in urls]
    await asyncio.gather(*tasks)

    # After processing all URLs, check if any remaining actions need to be indexed
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

    # Define the target Elasticsearch index
    TARGET_INDEX = 'raw2'

    es_client = ServiceUtils.initialize_es_client(ELASTICSEARCH_HOST, ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD)
    logging.info('Testing Elasticsearch connection')
    try:
        info = es_client.info()
        logging.info(f'Connected to Elasticsearch: {info}')
    except Exception as e:
        logging.critical(f'Could not connect to Elasticsearch: {e}')
        sys.exit(1)

    async with aiohttp.ClientSession() as session:
        # Check if backup processing is enabled via environment variable
        BACKUP = os.getenv('BACKUP')
        if BACKUP == 'True':
            if not es_client.indices.exists(index=TARGET_INDEX):
                es_client.indices.create(index=TARGET_INDEX)

            # Process various backup files containing benign and malicious URLs (One time use in case the database is cleared)
            logging.info("Processing benign URLs from 'PhiUSIIL - benign.txt'")
            await fetch_and_index_urls(es_client, session, 'backups/PhiUSIIL - benign.txt', TARGET_INDEX, False, 0, False)
            
            logging.info("Processing malicious URLs from 'PhiUSIIL - malicious.txt'")
            await fetch_and_index_urls(es_client, session, 'backups/PhiUSIIL - malicious.txt', TARGET_INDEX, False, 1, False)

            logging.info("Processing benign URLs for 'benign-top-1000000-1.txt'")
            await fetch_and_index_urls(es_client, session, 'backups/benign-top-1000000-1.txt', TARGET_INDEX, False, 0, False)

            logging.info("Processing benign URLs for 'mendeley benign - Webpages_Classification_test_data-1.txt'")
            await fetch_and_index_urls(es_client, session, 'backups/mendeley benign - Webpages_Classification_test_data-1.txt', TARGET_INDEX, False, 0, False)

            logging.info("Processing malicious URLs for 'openphish.txt'")
            await fetch_and_index_urls(es_client, session, 'backups/openphish.txt', TARGET_INDEX, False, 1, False)

        logging.info(f'Processing malicious URLs for {OPENFISH_URL}') 
        await fetch_and_index_urls(es_client, session, OPENFISH_URL, TARGET_INDEX, False, 1, True)

        logging.info(f'Processing malicious URLs for {PHISHING_DATABASE_URL}')
        await fetch_and_index_urls(es_client, session, PHISHING_DATABASE_URL, TARGET_INDEX, True, 1, True)

    logging.info('Completed all tasks.')

if __name__ == '__main__':
    asyncio.run(main())
