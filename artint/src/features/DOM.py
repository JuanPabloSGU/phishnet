import sys
import os
import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
from aiohttp import ClientTimeout

# Add the base directory 'phishnet' to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
phishnet_dir = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if phishnet_dir not in sys.path:
    sys.path.append(phishnet_dir)

from artint.src.features.ApiKeyManager import ApiKeyManager, AllApiKeysRateLimited
from gathering.utils import generate_user_agent

logging.basicConfig(level=logging.INFO)

class DOM:
    def __init__(self, session: aiohttp.ClientSession, api_key_manager: ApiKeyManager) -> None:
        self.api_key_manager = api_key_manager
        self.session = session
        self.user_agent = generate_user_agent()
        self.feat_dict = {}

    def initialize_feat_dict(self, url):
        self.feat_dict = {'url': url}
        feature_names = [
            'dom_total_nodes',
            'dom_max_depth',
            'dom_average_depth',
            'dom_unique_tags',
            'dom_num_comments',
            'dom_has_canvas',
            'dom_has_video',
            'dom_has_audio',
            'dom_total_attributes',
            'dom_average_attributes',
            'dom_inline_event_handlers',
            'dom_deprecated_tags_used',
            'dom_num_script_tags',
            'dom_screenshot_url'
        ]
        for feature in feature_names:
            # Initialize 'dom_screenshot_url' as an empty string, others as -1
            self.feat_dict[feature] = -1 if feature != 'dom_screenshot_url' else ''

    async def submit_url(self, url: str):
        while True:
            try:
                api_key = await self.api_key_manager.get_api_key()
            except AllApiKeysRateLimited:
                logging.error("STOPPING EXECUTION - ALL API KEYS RATE LIMITED")
                raise

            headers = {
                'User-Agent': self.user_agent,
                'Content-Type': 'application/json',
                'API-Key': api_key
            }

            data = {"url": url, "visibility": "public"}
            try:
                async with self.session.post("https://urlscan.io/api/v1/scan/", headers=headers, json=data, timeout=ClientTimeout(total=60)) as response:
                    status = response.status
                    match status:
                        case 200:
                            try:
                                response_json = await response.json()
                                uuid = response_json["uuid"]
                                return uuid
                            except KeyError:
                                logging.error(f"DOM.py: 'uuid' key not found in response for URL: {url}")
                                return None
                            except Exception:
                                logging.error(f"DOM.py: URL skipped: {url} - Unexpected exception occurred")
                                return None
                        case 400:
                            logging.warning(f"DOM.py: Skipping {url}, urlscan.io cannot process this URL.")
                            return None
                        case 429:
                            logging.warning(f"DOM.py: Rate limited by urlscan.io when submitting URL: {url}")
                            await self.api_key_manager.mark_rate_limited(api_key)
                            continue  # Try with another API key
                        case _:
                            logging.error(f"DOM.py: Unexpected status code {response.status} when submitting URL: {url}")
                            return None
            except asyncio.TimeoutError:
                logging.error(f"DOM.py: Request timed out when submitting URL: {url}")
                return None
            except aiohttp.ClientError:
                logging.error(f"DOM.py: Client error occurred when submitting URL {url}")
                return None
            except Exception:
                logging.error(f"DOM.py: Unexpected error occurred when submitting URL {url}")
                return None

    async def get_result(self, uuid: str, retries: int):
        url = f"https://urlscan.io/api/v1/result/{uuid}/"
        for idx in range(retries):
            try:
                api_key = await self.api_key_manager.get_api_key()
            except AllApiKeysRateLimited:
                logging.error("STOPPING EXECUTION - ALL API KEYS RATE LIMITED")
                raise

            headers = {
                'User-Agent': self.user_agent,
                'API-Key': api_key
            }

            retry_delay = min(3**idx, 15)
            logging.info(f"DOM.py: Attempt {idx + 1}/{retries}: Fetching result for UUID {uuid}")
            try:
                async with self.session.get(url, headers=headers, timeout=ClientTimeout(total=60)) as response:
                    status = response.status
                    if status == 200:
                        result = await response.json()
                        return result
                    elif status == 404:
                        # The scan is not ready yet; wait and retry
                        await asyncio.sleep(retry_delay)
                        continue
                    elif status == 429:
                        logging.warning("DOM.py: Rate limited by urlscan.io when fetching result.")
                        await self.api_key_manager.mark_rate_limited(api_key)
                        continue  # Try with another API key
                    else:
                        logging.error(f"DOM.py: Error fetching result for UUID {uuid}: HTTP {response.status}")
                        return None
            except aiohttp.ClientError:
                logging.error(f"DOM.py: Client error occurred when fetching result for UUID {uuid}")
                return None
            except asyncio.TimeoutError:
                logging.error(f"DOM.py: Request timed out when fetching result for UUID {uuid}")
                return None
        logging.error(f"DOM.py: Exceeded maximum retries ({retries}) for UUID {uuid}.")
        return None

    async def get_dom_snapshot(self, uuid: str, retries: int):
        url = f"https://urlscan.io/dom/{uuid}/"
        for idx in range(retries):
            try:
                api_key = await self.api_key_manager.get_api_key()
            except AllApiKeysRateLimited:
                logging.error("STOPPING EXECUTION - ALL API KEYS RATE LIMITED")
                raise

            headers = {
                'User-Agent': self.user_agent,
                'API-Key': api_key
            }

            retry_delay = min(3**idx, 15)
            logging.info(f"DOM.py: Attempt {idx + 1}/{retries}: Fetching DOM snapshot for UUID {uuid}")
            try:
                async with self.session.get(url, headers=headers, timeout=ClientTimeout(total=60)) as response:
                    status = response.status
                    if status == 200:
                        dom_content = await response.text()
                        return dom_content
                    elif status == 404:
                        # The DOM snapshot is not ready yet; wait and retry
                        await asyncio.sleep(retry_delay)
                        continue
                    elif status == 429:
                        logging.warning("DOM.py: Rate limited by urlscan.io when fetching DOM snapshot.")
                        await self.api_key_manager.mark_rate_limited(api_key)
                        continue  # Try with another API key
                    else:
                        logging.error(f"DOM.py: Error fetching DOM snapshot for UUID {uuid}: HTTP {response.status}")
                        return None
            except aiohttp.ClientError:
                logging.error(f"DOM.py: Client error occurred when fetching DOM snapshot for UUID {uuid}")
                return None
            except asyncio.TimeoutError:
                logging.error(f"DOM.py: Request timed out when fetching DOM snapshot for UUID {uuid}")
                return None
        logging.error(f"DOM.py: Exceeded maximum retries ({retries}) for UUID {uuid} when fetching DOM snapshot.")
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
        self.initialize_feat_dict(url)
        try:
            uuid = await self.submit_url(url)
            if not uuid:
                logging.error(f"DOM.py: Failed to submit URL: {url}")
                return self.feat_dict
            logging.info(f"DOM.py: Submitted URL: {url}, UUID: {uuid}")

            # Waiting 5 seconds before checking the result
            await asyncio.sleep(5)

            result = await self.get_result(uuid, retries=5)
            if not result:
                logging.error(f"DOM.py: No result obtained for UUID {uuid}")
                return self.feat_dict

            dom_content = await self.get_dom_snapshot(uuid, retries=5)
            if not dom_content:
                logging.error(f"DOM.py: No DOM content obtained for UUID {uuid}")
                return self.feat_dict

            await self.extract_dom_features(dom_content)
            self.feat_dict['dom_screenshot_url'] = f"https://urlscan.io/screenshots/{uuid}.png"

            logging.info(f'DOM.py: Successfully returned DOM features for url: {url}')
            return self.feat_dict
        
        except AllApiKeysRateLimited:
            logging.error(f"DOM.py: All API keys are rate-limited for URL {url}")
            raise

        except Exception:
            logging.error(f"DOM.py: Error processing URL {url}", exc_info=True)
            return self.feat_dict