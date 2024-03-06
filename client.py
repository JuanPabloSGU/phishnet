# TODO: 
# - Finish integrating with ELK stack
# - Testing

import logging
import socket
import requests
import json
import sys
import time
import logging.handlers
from minio import Minio
from minio.error import ResponseError

# Server IP and port
SERVER_IP = "172.105.102.230"
PORT_NO = 8889

# Logstash host and port
LOGSTASH_HOST = "" # Update logstash credentials
LOGSTASH_PORT = 5000 # Update logstash credentials

# S3 configuration
S3_HOST = "minio.databending.ca"
S3_BUCKET = "capstone"

# Configure logging
logging.basicConfig(filename='client.log', level=logging.INFO)

# Check if API keys are provided as command-line arguments
if len(sys.argv) != 3:
    print("Usage: python client.py <API_KEY_URLSCAN> <API_KEY_GSB>")
    sys.exit(1)

API_KEY_URLSCAN = sys.argv[1]
API_KEY_GSB = sys.argv[2]

# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
client_socket.connect((SERVER_IP, PORT_NO))

# Create a Logstash handler
logstash_handler = logging.handlers.SysLogHandler(address=(LOGSTASH_HOST, LOGSTASH_PORT))

# Add Logstash handler to the root logger
logging.getLogger().addHandler(logstash_handler)

# Function to upload file to S3 bucket
def upload_to_s3(filename, data):
    try:
        minio_client = Minio(S3_HOST, access_key='capstone', secret_key='dwU4hSc2sOc3YdO3qJV7ga3kW2UvKhjs', secure=False)
        # Upload data to S3 bucket
        minio_client.put_object(S3_BUCKET, filename, data, length=len(data))
    
    except ResponseError as err:
        logging.error(err)

# Function to process URLs
def process_urls(urls):
    for url in urls:
        try:
            # Submit URL to urlscan.io
            headers = {'API-Key':API_KEY_URLSCAN,'Content-Type':'application/json'}
            data={"url": url, "visibility": "public"}
            response = requests.post("https://urlscan.io/api/v1/scan/", headers=headers, data=json.dumps(data))
            response_json = response.json()

            # If the response is 400, skip processing
            if response.status_code == 400:
                logging.warning(f"Skipping {url}, urlscan.io cannot process this URL.")
                continue

            uuid = response_json["uuid"]

            # Log URL and UUID
            logging.info(f"Processing URL: {url}, UUID: {uuid}")

            # URLScan recommends to sleep 2 seconds before checking the result
            time.sleep(2)

            # Get the result from urlscan.io
            urlscan_response = requests.get(f"https://urlscan.io/api/v1/result/{uuid}/").json()

            # Log URLScan response
            logging.info("URLScan response: %s", json.dumps(urlscan_response))

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

            # Log Google Safe Browsing response
            logging.info("Google Safe Browsing response: %s", json.dumps(gsb_response))

            # Upload HTML snapshot to S3 bucket via MinIO
            html_snapshot = requests.get(f"https://urlscan.io/dom/{uuid}/").content
            upload_to_s3(f"{uuid}.html", html_snapshot)

            # Upload PNG screenshot to S3 bucket via MinIO
            png_screenshot = requests.get(f"https://urlscan.io/screenshots/{uuid}.png").content
            upload_to_s3(f"{uuid}.png", png_screenshot)

        except Exception as e:
            logging.error(f"Error processing URL {url}: {e}")

# Receive URLs from the server
while True:
    url_data = client_socket.recv(1024).decode()
    if not url_data:
        break
    urls = url_data.splitlines()

    process_urls(urls)

    # Send acknowledgment back to the server
    client_socket.send(b"URLs processed successfully")

client_socket.close()