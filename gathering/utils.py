import asyncio
import aiohttp
import logging
import random
import re
import requests

# Helper function to download data from a URL
def download_from_url(url, stream):
    logging.info(f"Downloading data from {url}")
    response = requests.get(url, stream=stream)
    if response.status_code != 200:
        logging.critical(f"Failed to download file from {url}")
        return None
    return response

def generate_user_agent() -> str:
    """
    Generate a random user agent.
    """
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.134 Mobile Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.109 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.2151.58',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.2151.58',
        'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.134 Mobile Safari/537.36 EdgA/118.0.2088.66',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 EdgiOS/119.2151.65 Mobile/15E148 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (Android 14; Mobile; rv:109.0) Gecko/119.0 Firefox/119.0',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/119.0 Mobile/15E148 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0',
        'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.134 Mobile Safari/537.36 OPR/76.2.4027.73374',
        'Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko'
    ]

    return random.choice(user_agents)

# Helper function to add scheme to a URL for consistency
async def preprocess_url(session, url):
    headers = {
        'User-Agent': generate_user_agent()
    }
    # Add scheme if missing
    if not re.match(r'^(http|https)://', url):
        https_url = 'https://' + url
        try:
            # Attempt to fetch the URL with HTTPS
            response = await session.head(https_url, headers=headers, timeout=5, allow_redirects=True)
            if response.status < 400:
                return https_url
            else:
                http_url = 'http://' + url
        except Exception as e:
            # HTTPS failed, try HTTP
            http_url = 'http://' + url
    else:
        http_url = url

    try:
        # Attempt to fetch the URL with HTTP
        response = await session.head(http_url, headers=headers, timeout=5, allow_redirects=True)
        if response.status < 400:
            return http_url
        else:
            logging.warning(f"URL skipped: {http_url} - Received status code: {response.status}")
            return None
    # Skip the URL if an Exception or Error occurred
    except asyncio.TimeoutError:
        logging.warning(f"URL skipped: {http_url} - Timeout occurred")
        return None
    except asyncio.CancelledError:
        logging.warning(f"URL skipped: {url} - Request was cancelled")
        return None
    except aiohttp.ClientError as e:
        logging.warning(f"URL skipped: {http_url} - Client error occurred: {e}")
        return None
    except Exception as e:
        logging.error(f"URL skipped: {http_url} - Unexpected exception occurred: {e}")
        return None