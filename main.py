import os
import requests
import json
import sys
import time
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from minio import Minio
from minio.error import ResponseError

load_dotenv()

# Elasticsearch host and port (update with correct credentials)
ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST')
ELASTICSEARCH_INDEX = os.getenv('ELASTICSEARCH_INDEX')

# S3 configuration
S3_HOST = os.getenv('S3_HOST')
S3_BUCKET = os.getenv('S3_BUCKET')

# Check if API keys are provided as command-line arguments
if len(sys.argv) != 5:
    print("Usage: python main.py <API_KEY_URLSCAN> <API_KEY_GSB> <ACCESS_KEY> <SECRET_KEY>")
    sys.exit(1)

API_KEY_URLSCAN = os.getenv('URLSCAN_API_KEY')
API_KEY_GSB = os.getenv('GOOGLE_SAFE_BROWSING_API_KEY')
ACCESS_KEY = os.getenv('MINIO_ACCESS')
SECRET_KEY = os.getenv('MINIO_SECRET')

data_sources = [
    "https://raw.githubusercontent.com/mitchellkrogza/Phishing.Database/master/phishing-links-ACTIVE.txt"
]

# Create Elasticsearch client
es_client = Elasticsearch(ELASTICSEARCH_HOST)

# Function to upload file to S3 bucket
def upload_to_s3(filename, data):
    try:
        minio_client = Minio(S3_HOST, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)
        minio_client.put_object(S3_BUCKET, filename, data, length=len(data))
    
    except ResponseError as err:
        print(err)

# Function to process URLs
def process_url(url):
    try:
        # Submit URL to urlscan.io
        headers = {'API-Key':API_KEY_URLSCAN,'Content-Type':'application/json'}
        data={"url": url, "visibility": "public"}
        response = requests.post("https://urlscan.io/api/v1/scan/", headers=headers, data=json.dumps(data))
        response_json = response.json()

        # If the response is 400, skip processing
        if response.status_code == 400:
            print(f"Skipping {url}, urlscan.io cannot process this URL.")
            return

        uuid = response_json["uuid"]

        # TODO: Remove later - print statement for testing purposes 
        print(f"Processing URL: {url}, UUID: {uuid}")

        # URLScan recommends to sleep 2 seconds before checking the result
        time.sleep(2)

        # Get the result from urlscan.io
        urlscan_response = requests.get(f"https://urlscan.io/api/v1/result/{uuid}/").json()

        # TODO: Remove later - print statement for testing purposes 
        print("URLScan response: %s", json.dumps(urlscan_response))

        # Prepare request body for Google Safe Browsing API
        request_body = {
            "client": {"clientId": "Capstone", "clientVersion": "1.5.2"},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": urlscan_response["page"]["url"]}]
            }
        }

        # Send request to Google Safe Browsing API
        gsb_response = requests.post(
            f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={API_KEY_GSB}",
            json=request_body
        ).json()

        # TODO: Remove later - print statement for testing purposes 
        print("Google Safe Browsing response: %s", json.dumps(gsb_response))

        # Index data to Elasticsearch
        data = {
            "url": url,
            "uuid": uuid,
            "urlscan_response": urlscan_response,
            "gsb_response": gsb_response
        }
        es_client.index(index=ELASTICSEARCH_INDEX, body=data)

        # Upload HTML snapshot to S3 bucket via MinIO
        html_snapshot = requests.get(f"https://urlscan.io/dom/{uuid}/").content
        upload_to_s3(f"{uuid}.html", html_snapshot)

        # Upload PNG screenshot to S3 bucket via MinIO
        png_screenshot = requests.get(f"https://urlscan.io/screenshots/{uuid}.png").content
        upload_to_s3(f"{uuid}.png", png_screenshot)

    except Exception as e:
        print(f"Error processing URL {url}: {e}")

# Process URLs from data_sources
for source in data_sources:
    response = requests.get(source)
    urls = response.text.splitlines()
    for url in urls:
        process_url(url)