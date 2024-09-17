import asyncio
import aiohttp
import csv
import hashlib
import logging
import re
import requests
import socket
import sys
from elasticsearch import helpers

# Setting the maximum limit for field size
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    # If the max size is too large, set the limit to the max 32-bit signed integer
    csv.field_size_limit(2**31 - 1)

# Helper function to load a CSV file into Elasticsearch
def load_csv_to_es(file_name, es_client, data_index):
    logging.info(f"Loading {file_name} into Elasticsearch")
    actions = []

    # Open the CSV file and create a dictionary reader
    with open(file_name, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row['url']
            type = int(row['type'])
            # Generate a hash of the URL to use as the document ID
            url_id = hashlib.sha256(url.encode('utf-8')).hexdigest()
            
            action = {
                '_index': data_index,
                '_id': url_id,
                '_source': {
                    'url': url,
                    'type': type
                }
            }
            actions.append(action)

    # Use the Elasticsearch helpers to bulk load the data into the index
    try:
        helpers.bulk(es_client, actions)
        logging.info(f"Completed loading {file_name} into Elasticsearch")
    except Exception as e:
        logging.error(f"Error loading {file_name} into Elasticsearch: {e}")

# Helper function to download data from a URL
def download_from_url(url, stream):
    logging.info(f"Downloading data from {url}")
    response = requests.get(url, stream=stream)
    if response.status_code != 200:
        logging.critical(f"Failed to download file from {url}")
        return None
    return response

# Helper function to add scheme to a URL for consistency
async def preprocess_url(session, url):
    # Add scheme if missing
    if not re.match(r'^(http|https)://', url):
        https_url = 'https://' + url
        try:
            # Attempt to fetch the URL with HTTPS
            response = await session.head(https_url, timeout=3, allow_redirects=True)
            if response.status < 400:
                return https_url
            else:
                http_url = 'http://' + url
        except Exception as e:
            http_url = 'http://' + url
    else:
        http_url = url

    try:
        # Attempt to fetch the URL with HTTP
        response = await session.head(http_url, timeout=3, allow_redirects=True)
        if response.status < 400:
            return http_url
        else:
            logging.warning(f"URL skipped: {http_url} - Received status code: {response.status}")
            return None
    except Exception as e:
        logging.warning(f"URL skipped: {http_url} - Exception occurred: {e}")
        return None  # Skip the URL if both HTTPS and HTTP failed