import sys
import os
import aiohttp
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from gathering.utils import generate_user_agent

class DOM:
    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        self.API_KEY_URLSCAN = api_key
        self.session = session
        self.user_agent = generate_user_agent()
        self.headers = {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json',
            'API-Key': self.API_KEY_URLSCAN
        }
        self.feat_dict = {}

    async def submit_url(self, url: str):
        data = {"url": url, "visibility": "public"}
        async with self.session.post("https://urlscan.io/api/v1/scan/", headers=self.headers, json=data, timeout=15) as response:
            if response.status == 429:
                logging.warning(f"Rate limited by urlscan.io when submitting URL: {url}")
                return None
            elif response.status == 400:
                logging.warning(f"Skipping {url}, urlscan.io cannot process this URL.")
                return None
            elif response.status != 200:
                logging.error(f"Unexpected status code {response.status} when submitting URL: {url}")
                return None
            
            try:
                response_json = await response.json()
                uuid = response_json["uuid"]
                return uuid
            except KeyError:
                logging.error(f"'uuid' key not found in response for URL: {url}")
                return None
            except Exception as e:
                logging.error(f"DOM.py: URL skipped: {url} - Unexpected exception occurred: {e}")
                return None

    async def get_result(self, uuid: str, retries: int):
        url = f"https://urlscan.io/api/v1/result/{uuid}/"
        for idx in range(retries):
            retry_delay = min(3**idx, 15)
            logging.info(f"Attempt {idx + 1}/{retries}: Fetching result for UUID {uuid}")
            try: 
                async with self.session.get(url, timeout=15) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    elif response.status == 404:
                        # The scan is not ready yet; wait and retry
                        await asyncio.sleep(retry_delay)
                        continue
                    elif response.status == 429:
                        logging.warning("Rate limited by urlscan.io when fetching result.")
                        return None
                    else:
                        logging.error(f"Error fetching result for UUID {uuid}: HTTP {response.status}")
                        return None
            except aiohttp.ClientError as e:
                logging.error(f"Client error occurred when fetching result for UUID {uuid}: {e}")
                return None
            except asyncio.TimeoutError:
                logging.error(f"Request timed out when fetching result for UUID {uuid}")
                return None
        logging.error(f"Exceeded maximum retries ({retries}) for UUID {uuid}.")
        return None

    async def get_dom_snapshot(self, uuid: str):
        url = f"https://urlscan.io/dom/{uuid}/"
        logging.info(f"Fetching DOM snapshot for UUID {uuid}")
        try: 
            async with self.session.get(url, timeout=15) as response:
                if response.status == 200:
                    dom_content = await response.text()
                    return dom_content
                else:
                    logging.error(f"Error fetching DOM snapshot for UUID {uuid}: HTTP {response.status}")
                    return None
        except aiohttp.ClientError as e:
            logging.error(f"Client error occurred when fetching DOM snapshot for UUID {uuid}: {e}")
            return None
        except asyncio.TimeoutError:
            logging.error(f"Request timed out when fetching DOM snapshot for UUID {uuid}")
            return None

    async def extract_dom_features(self, dom_content: str):
        # Need helper functions for DOM feature extraction
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(dom_content, 'html.parser')
        self.feat_dict['dom_num_script_tags'] = len(soup.find_all('script'))

    async def extract(self, url: str):
        self.feat_dict['url'] = url
        try:
            uuid = await self.submit_url(url)
            if not uuid:
                logging.error(f"DOM.py: Failed to submit URL: {url}")
                return {}
            logging.info(f"Submitted URL: {url}, UUID: {uuid}")

            # Waiting 5 seconds before checking the result
            await asyncio.sleep(5)

            result = await self.get_result(uuid, retries=3)
            if not result:
                logging.error(f"No result obtained for UUID {uuid}")
                return {}

            dom_content = await self.get_dom_snapshot(uuid)
            if not dom_content:
                logging.error(f"No DOM content obtained for UUID {uuid}")
                return {}

            await self.extract_dom_features(dom_content)
            return self.feat_dict

        except Exception as e:
            logging.error(f"DOM.py: Error processing URL {url}: {e}", exc_info=True)
            return {}

# For testing purposes
# async def run_example():
#     # Paste your API key here (don't commit to GitHub)
#     API_KEY_URLSCAN = '1'

#     async with aiohttp.ClientSession() as session:
#         example = DOM(session, API_KEY_URLSCAN)
#         url = 'https://afmeldeninfo.com/unsubs-be-nee'
#         features = await example.extract(url)

#         for key, value in features.items():
#             print(f"{key}: {value}")

# asyncio.run(run_example())