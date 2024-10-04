import sys
import os
import aiohttp
import asyncio
import logging
import ApiKeyManager
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from gathering.utils import generate_user_agent

class DOM:
    def __init__(self, session: aiohttp.ClientSession, api_key_manager: ApiKeyManager) -> None:
        self.api_key_manager = api_key_manager
        self.session = session
        self.user_agent = generate_user_agent()
        self.feat_dict = {}

    async def submit_url(self, url: str):
        while True:
            api_key = await self.api_key_manager.get_api_key()
            if api_key is None:
                logging.error("No available API keys to submit URL: %s", url)
                return None

            headers = {
                'User-Agent': self.user_agent,
                'Content-Type': 'application/json',
                'API-Key': api_key
            }

            data = {"url": url, "visibility": "public"}
            async with self.session.post("https://urlscan.io/api/v1/scan/", headers=headers, json=data, timeout=15) as response:
                status = response.status
                match status:
                    case 200:
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
                    case 400:
                        logging.warning(f"Skipping {url}, urlscan.io cannot process this URL.")
                        return None
                    case 429:
                        logging.warning(f"Rate limited by urlscan.io when submitting URL: {url}")
                        await self.api_key_manager.mark_rate_limited(api_key)
                        continue # Try with another API key
                    case _:
                        logging.error(f"Unexpected status code {response.status} when submitting URL: {url}")
                        return None

    async def get_result(self, uuid: str, retries: int):
        url = f"https://urlscan.io/api/v1/result/{uuid}/"
        for idx in range(retries):
            api_key = await self.api_key_manager.get_api_key()
            if api_key is None:
                logging.error("No available API keys to fetch result for UUID: %s", uuid)
                return None

            headers = {
                'User-Agent': self.user_agent,
                'API-Key': api_key
            }

            retry_delay = min(3**idx, 15)
            logging.info(f"Attempt {idx + 1}/{retries}: Fetching result for UUID {uuid}")
            try:
                async with self.session.get(url, headers=headers, timeout=15) as response:
                    status = response.status
                    if status == 200:
                        result = await response.json()
                        return result
                    elif status == 404:
                        # The scan is not ready yet; wait and retry
                        await asyncio.sleep(retry_delay)
                        continue
                    elif status == 429:
                        logging.warning("Rate limited by urlscan.io when fetching result.")
                        await self.api_key_manager.mark_rate_limited(api_key)
                        continue  # Try with another API key
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

    async def get_dom_snapshot(self, uuid: str, retries: int):
        url = f"https://urlscan.io/dom/{uuid}/"
        for idx in range(retries):
            api_key = await self.api_key_manager.get_api_key()
            if api_key is None:
                logging.error("No available API keys to fetch DOM snapshot for UUID: %s", uuid)
                return None

            headers = {
                'User-Agent': self.user_agent,
                'API-Key': api_key
            }

            retry_delay = min(3**idx, 15)
            logging.info(f"Attempt {idx + 1}/{retries}: Fetching DOM snapshot for UUID {uuid}")
            try:
                async with self.session.get(url, headers=headers, timeout=15) as response:
                    status = response.status
                    if status == 200:
                        dom_content = await response.text()
                        return dom_content
                    elif status == 404:
                        # The DOM snapshot is not ready yet; wait and retry
                        await asyncio.sleep(retry_delay)
                        continue
                    elif status == 429:
                        logging.warning("Rate limited by urlscan.io when fetching DOM snapshot.")
                        await self.api_key_manager.mark_rate_limited(api_key)
                        continue  # Try with another API key
                    else:
                        logging.error(f"Error fetching DOM snapshot for UUID {uuid}: HTTP {response.status}")
                        return None
            except aiohttp.ClientError as e:
                logging.error(f"Client error occurred when fetching DOM snapshot for UUID {uuid}: {e}")
                return None
            except asyncio.TimeoutError:
                logging.error(f"Request timed out when fetching DOM snapshot for UUID {uuid}")
                return None
        logging.error(f"Exceeded maximum retries ({retries}) for UUID {uuid} when fetching DOM snapshot.")
        return None

    async def extract_dom_features(self, dom_content: str):
        soup = await asyncio.to_thread(BeautifulSoup, dom_content, 'html.parser')

        self.feat_dict['dom_total_nodes'] = self.get_total_nodes(soup)
        self.feat_dict['dom_max_depth'] = self.get_max_depth(soup)
        self.feat_dict['dom_average_depth'] = self.get_average_depth(soup)
        self.feat_dict['dom_unique_tags'] = self.get_unique_tags(soup)
        self.feat_dict['dom_num_comments'] = self.get_num_comments(soup)
        self.feat_dict['dom_has_canvas'] = self.has_element(soup, 'canvas')
        self.feat_dict['dom_has_video'] = self.has_element(soup, 'video')
        self.feat_dict['dom_has_audio'] = self.has_element(soup, 'audio')
        self.feat_dict['dom_total_attributes'] = self.get_total_attributes(soup)
        self.feat_dict['dom_average_attributes'] = self.get_average_attributes(soup)
        self.feat_dict['dom_inline_event_handlers'] = self.get_inline_event_handlers(soup)
        self.feat_dict['dom_deprecated_tags_used'] = self.get_deprecated_tags_used(soup)
        self.feat_dict['dom_num_script_tags'] = len(soup.find_all('script'))

    def get_total_nodes(self, soup):
        return len(soup.find_all())

    def get_max_depth(self, soup):
        def helper(node, current_depth=0):
            if not hasattr(node, 'contents') or not node.contents:
                return current_depth
            else:
                return max(helper(child, current_depth + 1) for child in node.contents if hasattr(child, 'name'))
        return helper(soup)

    def get_average_depth(self, soup):
        depths = []

        def helper(node, current_depth=0):
            if hasattr(node, 'contents') and node.contents:
                for child in node.contents:
                    if hasattr(child, 'name'):
                        depths.append(current_depth + 1)
                        helper(child, current_depth + 1)

        helper(soup)
        return sum(depths) / len(depths) if depths else 0

    def get_unique_tags(self, soup):
        tags = {tag.name for tag in soup.find_all()}
        return len(tags)

    def get_num_comments(self, soup):
        comments = soup.find_all(string=lambda text: isinstance(text, type(soup.comment)))
        return len(comments)

    def has_element(self, soup, tag_name):
        return 1 if soup.find(tag_name) else 0

    def get_total_attributes(self, soup):
        return sum(len(tag.attrs) for tag in soup.find_all())

    def get_average_attributes(self, soup):
        total_attributes = self.get_total_attributes(soup)
        total_elements = len(soup.find_all())
        return total_attributes / total_elements if total_elements else 0

    def get_inline_event_handlers(self, soup):
        inline_events = ['onload', 'onerror', 'onclick', 'onmouseover', 'onmouseout', 'onkeydown', 'onkeyup']
        return sum(
            1 for tag in soup.find_all() for attr in inline_events if attr in tag.attrs
        )

    def get_deprecated_tags_used(self, soup):
        deprecated_tags = ['applet', 'basefont', 'center', 'dir', 'font', 'frame', 'frameset',
                           'isindex', 'menu', 'noframes', 's', 'strike', 'u']
        return sum(1 for tag in deprecated_tags if soup.find(tag))

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

            dom_content = await self.get_dom_snapshot(uuid, retries=3)
            if not dom_content:
                logging.error(f"No DOM content obtained for UUID {uuid}")
                return {}

            await self.extract_dom_features(dom_content)
            self.feat_dict['dom_screenshot_url'] = f"https://urlscan.io/screenshots/{uuid}.png"

            return self.feat_dict

        except Exception as e:
            logging.error(f"DOM.py: Error processing URL {url}: {e}", exc_info=True)
            return {}

# For testing purposes
# async def run_example():
#     # Paste your API key here (don't commit to GitHub)
#     API_KEY_URLSCAN = ''

#     async with aiohttp.ClientSession() as session:
#         example = DOM(session, API_KEY_URLSCAN)
#         url = 'https://account.sunantamadaan.com'
#         features = await example.extract(url)

#         for key, value in features.items():
#             print(f"{key}: {value}")

# asyncio.run(run_example())