import sys
import os
import aiohttp
import asyncio
import hashlib
import logging
import io
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

# Add the parent directory to the system path to import utility modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import utilities.ServiceUtils as ServiceUtils
from artint.src.features.ApiKeyManager import ApiKeyManager
from artint.src.features.DOM import DOM
from artint.src.features.Content import Content

# Configure logging
logging.basicConfig(level=logging.INFO)

async def fetch_dom_content(url, dom_extractor):
    """
    Fetches the DOM content of the given URL using the DOM extractor.
    """
    # Submit the URL to urlscan.io
    uuid = await dom_extractor.submit_url(url)
    if not uuid:
        logging.error(f"Failed to submit URL to urlscan.io: {url}")
        return None

    logging.info(f"Submitted URL to urlscan.io: {url} with UUID: {uuid}")

    # Wait before fetching results
    await asyncio.sleep(10)

    dom_content = await dom_extractor.get_dom_snapshot(uuid, retries=5)
    if not dom_content:
        logging.error(f"Failed to retrieve DOM content for URL: {url}")
        return None
    return dom_content

async def fetch_html_content(url, content_extractor):
    """
    Fetches the HTML content of the given URL using the Content extractor.
    """
    response_data = await content_extractor.make_request(url, timeout=15, retries=3)
    if not response_data:
        logging.error(f"Failed to retrieve HTML content for URL: {url}")
        return None
    html_content = response_data['content']
    return html_content

def upload_to_s3(data, object_name, content_type, s3_client, s3_bucket):
    """
    Uploads the given data to S3 with the specified object name and content type.
    """
    try:
        s3_client.put_object(
            s3_bucket,
            object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type
        )
        logging.info(f"Uploaded {object_name} to S3 bucket {s3_bucket}")
    except S3Error as e:
        logging.error(f"Failed to upload {object_name} to S3. Error: {e}")

async def upload_url_content(doc, session, api_key_manager, s3_client, s3_bucket):
    """
    Processes a single URL:
    - Retrieves the DOM content.
    - Retrieves the HTML content.
    - Uploads both to S3.
    """
    url = doc['url'].rstrip('/')
    url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()

    # Initialize feature extractors
    dom_extractor = DOM(session, api_key_manager)
    content_extractor = Content(session)

    # Fetch DOM content
    dom_content = await fetch_dom_content(url, dom_extractor)
    if dom_content is None:
        logging.error(f"Skipping URL due to failure in fetching DOM content: {url}")
        return

    # Fetch HTML content
    html_content = await fetch_html_content(url, content_extractor)
    if html_content is None:
        logging.error(f"Skipping URL due to failure in fetching HTML content: {url}")
        return

    # Prepare object names
    dom_object_name = f"{url_hash}_dom.html"
    html_object_name = f"{url_hash}_html.html"

    # Upload DOM content to S3
    upload_to_s3(dom_content.encode('utf-8'), dom_object_name, 'text/html', s3_client, s3_bucket)

    # Upload HTML content to S3
    upload_to_s3(html_content, html_object_name, 'text/html', s3_client, s3_bucket)

async def main():
    # Load environment variables
    load_dotenv(override=True)
    
    # Load environment variables
    ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST')
    ELASTICSEARCH_USER = os.getenv('ELASTICSEARCH_USER')
    ELASTICSEARCH_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD')
    SOURCE_INDEX = os.getenv('SOURCE_INDEX')

    S3_HOST = os.getenv('S3_HOST')
    S3_BUCKET = os.getenv('S3_BUCKET')
    ACCESS_KEY = os.getenv('ACCESS_KEY')
    SECRET_KEY = os.getenv('SECRET_KEY')

    API_KEYS_URLSCAN = os.getenv('URLSCAN_API_KEY').split(',')

    # Initialize Elasticsearch client
    es_client = ServiceUtils.initialize_es_client(
        ELASTICSEARCH_HOST, ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD
    )

    # Initialize Minio client
    s3_client = Minio(
        S3_HOST,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False  # Set to True if using HTTPS
    )

    # Create the bucket if it doesn't exist
    if not s3_client.bucket_exists(S3_BUCKET):
        s3_client.make_bucket(S3_BUCKET)

    # Retrieve all documents from the source Elasticsearch index
    raw_data = ServiceUtils.get_es_index(es_client, SOURCE_INDEX)

    # Extract 'url' from each document in the raw data
    source_docs = [
        {'url': doc['_source']['url']}
        for doc in raw_data
    ]
    logging.info(f'Number of documents in the source index: {len(source_docs)}')

    api_key_manager = ApiKeyManager(API_KEYS_URLSCAN)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for doc in source_docs:
            task = upload_url_content(doc, session, api_key_manager, s3_client, S3_BUCKET)
            tasks.append(task)
        # Limit the number of concurrent tasks to prevent overwhelming the system
        semaphore = asyncio.Semaphore(100)
        async def semaphore_task(task):
            async with semaphore:
                await task
        await asyncio.gather(*(semaphore_task(task) for task in tasks))

if __name__ == "__main__":
    asyncio.run(main())
