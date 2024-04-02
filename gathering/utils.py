import csv
import logging
import requests
import sys
from elasticsearch import helpers

# Setting the maximum limit for field size
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2**31 - 1)

def load_csv_to_es(file_name, es_client, data_index):
    logging.info(f"Loading {file_name} into Elasticsearch")
    with open(file_name, 'r') as f:
        reader = csv.DictReader(f)
        helpers.bulk(es_client, reader, index=data_index)

    logging.info(f"Completed loading {file_name} into Elasticsearch")

def download_from_url(url, stream):
    logging.info(f"Downloading data from {url}")
    response = requests.get(url, stream=stream)

    if response.status_code != 200:
        logging.critical(f"Failed to download file from {url}")

    return response