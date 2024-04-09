import csv
import logging
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

# Helper function to add a protocol to a URL if it is missing
def add_protocol(url):
    # If the URL doesn't start with 'http://' or 'https://', attempt to add one of these protocols
    if not url.startswith(('http://', 'https://')):
        for protocol in ['http://', 'https://']:
            try:
                # Send a GET request to the URL with the added protocol
                res = requests.get(protocol + url, timeout=1)

                # If the response status code is 200, the protocol was successfully added
                if res.status_code == 200:
                    logging.info("Added protocol to URL: %s", url)
                    return res.url
                else:
                    # If the response status code is not 200, return None
                    return None
            except Exception as e:
                logging.error("Error adding protocol to URL: %s", str(e))
                return None
    # If the URL already starts with 'http://' or 'https://', return it as is
    return url