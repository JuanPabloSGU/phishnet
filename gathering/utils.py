import csv
import requests
import logging
from elasticsearch import helpers

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

def get_protocol(url):
    if not url.startswith(('http://', 'https://')):
        try:
            res = requests.get('http://' + url, timeout=3)
            if res.status_code == 200: 
                return res.url
        except requests.exceptions.RequestException as e:
            return None

        try:
            res = requests.get('https://' + url, timeout=3)
            if res.status_code == 200:
                return res.url
        except requests.exceptions.RequestException as e:
            return None

    return url