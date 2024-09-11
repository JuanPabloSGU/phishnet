import aiohttp
import csv
import logging
import re
import requests
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

    # Open the CSV file and create a dictionary reader
    with open(file_name, 'r') as f:
        reader = csv.DictReader(f)
        # Use the Elasticsearch helpers to bulk load the CSV into the index
        helpers.bulk(es_client, reader, index=data_index)

    logging.info(f"Completed loading {file_name} into Elasticsearch")

# Helper function to download data from a URL
def download_from_url(url, stream):
    logging.info(f"Downloading data from {url}")

    # Send a GET request to the specified URL
    response = requests.get(url, stream=stream)

    if response.status_code != 200:
        logging.critical(f"Failed to download file from {url}")

    return response

# Helper function to add scheme and subdomain to a URL for consistency
async def preprocess_url(session, url):
    # Add scheme if missing
    if not re.match(r'^(http|https)://', url):
        # Try https first
        test_url = 'https://' + url
        try:
            async with session.get(test_url, timeout=1) as response:
                if response.status < 400:
                    url = test_url
                else:
                    url = 'http://' + url
        except aiohttp.ClientError:
            # If https fails, fall back to http
            url = 'http://' + url
    
    # Add 'www.' if missing
    if not re.match(r'^https?://www\.', url):
        url = re.sub(r'^(https?://)', r'\1www.', url)
    
    return url