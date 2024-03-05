# TODO: Integrate and test with ELK stack

import socket
import requests
import json
import sys
import time
import psycopg2
from psycopg2 import sql
from minio import Minio
from minio.error import ResponseError

# Server IP and port
SERVER_IP = "172.105.102.230"
PORT_NO = 8889

# Database credentials
DB_HOST = ""
DB_PORT = 12345
DB_USER = ""
DB_PASSWORD = ""
DB_NAME = ""

# S3 configuration
S3_HOST = "minio.databending.ca"
S3_BUCKET = "capstone"

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

# Function to insert URL and UUID into the database
def insert_into_db(url, uuid, metadata):
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        cursor = conn.cursor()

        insert_query = sql.SQL("INSERT INTO webscrape (url, id, metadata) VALUES (%s, %s, %s)")
        cursor.execute(insert_query, (url, uuid, json.dumps(metadata)))

        conn.commit()
    except Exception as e:
        print(f"Error inserting into database: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to upload file to S3 bucket
def upload_to_s3(filename, data):
    try:
        minio_client = Minio(S3_HOST, access_key='YOUR_ACCESS_KEY', secret_key='YOUR_SECRET_KEY', secure=False)
        # Upload data to S3 bucket
        minio_client.put_object(S3_BUCKET, filename, data, length=len(data))
        print(f"File {filename} uploaded to S3 successfully")
    
    except ResponseError as err:
        print(err)

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
                print(f"Skipping {url}, urlscan.io cannot process this URL.")
                continue

            uuid = response_json["uuid"]

            # Insert URL and UUID into database
            insert_into_db(url, uuid, response_json)

            # URLScan recommends to sleep 2 seconds before checking the result
            time.sleep(2)

            # Get the result from urlscan.io
            urlscan_response = requests.get(f"https://urlscan.io/api/v1/result/{uuid}/").json()

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

            if not gsb_response:
                print(f"The URL {url} is safe according to the Google Safe Browsing API.")
            else:
                print("The URL is potentially unsafe. Here's the response from the Google Safe Browsing API:")
                print(json.dumps(gsb_response, indent=4))

            # Insert responses into database
            insert_into_db(uuid, "urlscan_response", urlscan_response)
            insert_into_db(uuid, "gsb_response", gsb_response)

            # Upload HTML snapshot to S3 bucket via MinIO
            html_snapshot = requests.get(f"https://urlscan.io/dom/{uuid}/").content
            upload_to_s3(f"{uuid}.html", html_snapshot)

            # Upload PNG screenshot to S3 bucket via MinIO
            png_screenshot = requests.get(f"https://urlscan.io/screenshots/{uuid}.png").content
            upload_to_s3(f"{uuid}.png", png_screenshot)

        except Exception as e:
            print(f"Error processing URL {url}: {e}")

# Receive URLs from the server
while True:
    url_data = client_socket.recv(1024).decode()
    if not url_data:
        break
    urls = url_data.splitlines()

    print("Received URLs from server:")
    for url in urls:
        print(url)

    # Process URLs
    process_urls(urls)

    # Send acknowledgment back to the server
    client_socket.send(b"URLs processed successfully")

client_socket.close()