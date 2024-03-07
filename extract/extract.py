import requests
import os
from dotenv import load_dotenv

def extract(url: str):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f'Error: {response.status_code}')

    return response.json()

load_dotenv()

r = extract(os.getenv('BLOCKLIST'))