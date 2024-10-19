import asyncio
import aiohttp
import hashlib
import logging
import random
import re
import requests
from elasticsearch import Elasticsearch

def download_from_url(url, stream):
    """
    Downloads data from the specified URL.

    Parameters:
    url (str): The URL to download data from.
    stream (bool): If True, the response content will be streamed; otherwise, it will be downloaded immediately.

    Returns:
    Response object if the download is successful; otherwise, None.
    """
    logging.info(f"Downloading data from {url}")
    response = requests.get(url, stream=stream)
    if response.status_code != 200:
        logging.critical(f"Failed to download file from {url}")
        return None
    return response

def generate_user_agent() -> str:
    """
    Generates a random user agent string from a predefined list.

    Returns:
    str: A randomly selected user agent string.
    """
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.134 Mobile Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.109 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.2151.58',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.2151.58',
        'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.134 Mobile Safari/537.36 EdgA/118.0.2088.66',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 EdgiOS/119.2151.65 Mobile/15E148 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (Android 14; Mobile; rv:109.0) Gecko/119.0 Firefox/119.0',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/119.0 Mobile/15E148 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0',
        'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.134 Mobile Safari/537.36 OPR/76.2.4027.73374',
        'Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko'
    ]

    return random.choice(user_agents)

async def preprocess_url(session, url):
    """
    Preprocesses a URL by ensuring it has a valid HTTP or HTTPS scheme and verifying its accessibility.

    Parameters:
    session (aiohttp.ClientSession): The aiohttp session used to make HTTP requests.
    url (str): The URL to preprocess.

    Returns:
    str or None: The preprocessed and validated URL with scheme, or None if validation fails.
    """
    headers = {
        'User-Agent': generate_user_agent()
    }
    # Add scheme if missing
    if not re.match(r'^(http|https)://', url):
        https_url = 'https://' + url
        try:
            # Attempt to fetch the URL with HTTPS
            response = await session.head(https_url, headers=headers, timeout=15, allow_redirects=True)
            if response.status < 400:
                logging.info(f"HTTPS addition was valid: {https_url}")
                return https_url.rstrip('/')
            else:
                http_url = 'http://' + url
        except Exception as e:
            # HTTPS failed, try HTTP
            http_url = 'http://' + url
    else:
        http_url = url

    try:
        # Attempt to fetch the URL with HTTP
        response = await session.head(http_url, headers=headers, timeout=15, allow_redirects=True)
        if response.status < 400:
            logging.info(f"URL validated: {http_url}")
            return http_url.rstrip('/')
        else:
            logging.warning(f"URL skipped: {http_url} - Received status code: {response.status}")
            return None
    # Handle specific exceptions and skip the URL if they occur
    except asyncio.TimeoutError:
        logging.warning(f"URL skipped: {http_url} - Timeout occurred")
        return None
    except asyncio.CancelledError:
        logging.warning(f"URL skipped: {http_url} - Request was cancelled")
        return None
    except aiohttp.ClientError as e:
        logging.warning(f"URL skipped: {http_url} - Client error occurred: {e}")
        return None
    except Exception as e:
        logging.error(f"URL skipped: {http_url} - Unexpected exception occurred: {e}")
        return None
    
def initialize_es_client(host, user, password):
    """
    Initializes and returns an Elasticsearch client.

    Parameters:
    host (str): The Elasticsearch host URL.
    user (str): The username for Elasticsearch authentication.
    password (str): The password for Elasticsearch authentication.

    Returns:
    Elasticsearch: An instance of the Elasticsearch client.
    """
    logging.info('Connecting to Elasticsearch')
    es_client = Elasticsearch(
        host,
        basic_auth=(user, password),
        request_timeout=60
    )
    return es_client

def get_es_index(es, index):
    """
    Retrieves all documents from the specified Elasticsearch index.

    Parameters:
    es (Elasticsearch): The Elasticsearch client instance.
    index (str): The name of the Elasticsearch index to query.

    Returns:
    list: A list of all documents retrieved from the index.
    """
    try:
        logging.info('Getting all data from Elasticsearch index: %s', index)
        query = {"query": {"match_all": {}}}
        response = es.search(index=index, body=query, scroll='1m', size=5000)
        all_data = response['hits']['hits']
        while len(response['hits']['hits']):
            response = es.scroll(scroll_id=response['_scroll_id'], scroll='1m')
            all_data += response['hits']['hits']
        logging.info('Retrieved %d documents from Elasticsearch index: %s', len(all_data), index)
        return all_data
    finally:
        es.clear_scroll(scroll_id=response['_scroll_id'])

def get_all_ids(es, index):
    """
    Retrieves all document IDs (URL hashes) from the specified Elasticsearch index.

    Parameters:
    es (Elasticsearch): The Elasticsearch client instance.
    index (str): The name of the Elasticsearch index to query.

    Returns:
    set: A set of all document IDs (URL hashes) in the index.
    """
    logging.info('Getting all ids from Elasticsearch index: %s', index)
    query = {"stored_fields": [], "query": {"match_all": {}}}
    response = es.search(index=index, body=query, scroll='1m', size=5000)
    all_ids = [hit['_id'] for hit in response['hits']['hits']]
    while len(response['hits']['hits']):
        response = es.scroll(scroll_id=response['_scroll_id'], scroll='1m')
        all_ids += [hit['_id'] for hit in response['hits']['hits']]
    logging.info('Retrieved %d ids from Elasticsearch index: %s', len(all_ids), index)
    return set(all_ids)

def deduplicate_batch(docs_batch):
    """
    Deduplicates a batch of documents based on the SHA-256 hash of their URLs.

    Parameters:
    docs_batch (list): A list of document dictionaries, each containing a 'url' key.

    Returns:
    list: A deduplicated list of documents.
    """
    seen_hashes = set()
    deduplicated_docs = []
    for doc in docs_batch:
        url = doc['url'].rstrip('/')
        url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
        if url_hash not in seen_hashes:
            seen_hashes.add(url_hash)
            deduplicated_docs.append(doc)
    return deduplicated_docs

def check_failure(feature_dict):
    """
    Checks if at least 50% of the features in the provided dictionary have failed, used for statistics.

    Parameters:
    feature_dict (dict): A dictionary where each key represents a feature and its value indicates success or failure.

    Returns:
    bool: True if 50% or more of the features have failed; False otherwise.
    """
    total_features = len(feature_dict)
    if (total_features == 0): return False
    
    failed_features = sum(1 for value in feature_dict.values() if value == -1 or value == "-1")
    return failed_features >= total_features / 2