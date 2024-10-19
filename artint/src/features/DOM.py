import sys
import os
import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
from aiohttp import ClientTimeout

# Add the base directory 'phishnet' to sys.path to import utility functions
current_dir = os.path.dirname(os.path.abspath(__file__))
phishnet_dir = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if phishnet_dir not in sys.path:
    sys.path.append(phishnet_dir)

from artint.src.features.ApiKeyManager import ApiKeyManager
from utilities.ServiceUtils import generate_user_agent

logging.basicConfig(level=logging.INFO)

class DOM:
    """
    A class to extract various DOM-related features from a given URL's HTML content using the urlscan.io API.
    
    This class handles submitting URLs to urlscan.io, fetching the results, parsing the DOM content,
    and extracting specific features related to the structure and behavior of the DOM.
    """
    def __init__(self, session: aiohttp.ClientSession, api_key_manager: ApiKeyManager) -> None:
        """
        Initializes the DOM extractor with an aiohttp session and an API key manager.
        
        Parameters:
        session (aiohttp.ClientSession): An aiohttp session used for making HTTP requests.
        api_key_manager (ApiKeyManager): An instance of ApiKeyManager to manage API keys and handle rate-limiting.
        """
        self.api_key_manager = api_key_manager
        self.session = session
        self.user_agent = generate_user_agent()
        self.feat_dict = {} # Dictionary to store extracted DOM features

    def initialize_feat_dict(self, url):
        """
        Initializes the feature dictionary with default values for a given URL.
        
        Parameters:
        url (str): The URL for which DOM features are being extracted.
        """
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
        # Initialize all features to -1 or '-1' indicating default or unprocessed state
        for feature in feature_names:
            self.feat_dict[feature] = -1 if feature != 'dom_screenshot_url' else '-1'

    async def submit_url(self, url: str):
        """
        Submits a URL to the urlscan.io API for scanning.
        
        Parameters:
        url (str): The URL to submit for scanning.
        
        Returns:
        str or None: The UUID of the scan if submission is successful; otherwise, None.
        """
        while True:
            # Retrieve an available API key
            api_key = await self.api_key_manager.get_api_key()
            headers = {
                'User-Agent': self.user_agent,
                'Content-Type': 'application/json',
                'API-Key': api_key
            }

            data = {"url": url, "visibility": "public"}
            try:
                # Make a POST request to submit the URL for scanning
                async with self.session.post("https://urlscan.io/api/v1/scan/", headers=headers, json=data, timeout=ClientTimeout(total=60)) as response:
                    status = response.status
                    if status == 200:
                        response_json = await response.json()
                        uuid = response_json.get("uuid")
                        if uuid:
                            return uuid
                        else:
                            logging.error(f"DOM.py: 'uuid' key not found in response for URL: {url}")
                            return None
                    elif status == 400:
                        # Bad request; urlscan.io cannot process this URL
                        logging.warning(f"DOM.py: Skipping {url}, urlscan.io cannot process this URL.")
                        return None
                    elif status == 429:
                        # Rate limited; handle by marking the API key and retrying
                        reset_after = response.headers.get('X-Rate-Limit-Reset-After')
                        if reset_after is not None:
                            reset_after = int(reset_after)
                        else:
                            reset_after = 60 
                            logging.warning(f"DOM.py: 'X-Rate-Limit-Reset-After' header not found. Using default wait time of {reset_after} seconds.")
                        logging.warning(f"DOM.py: Rate limited by urlscan.io when submitting URL: {url}. Waiting for {reset_after} seconds.")
                        await self.api_key_manager.mark_rate_limited(api_key, reset_after)
                        continue  # Try with another API key
                    else:
                        # Unexpected status code
                        logging.error(f"DOM.py: Unexpected status code {response.status} when submitting URL: {url}")
                        return None
            except asyncio.TimeoutError:
                logging.error(f"DOM.py: Request timed out when submitting URL: {url}")
                return None
            except aiohttp.ClientError as e:
                logging.error(f"DOM.py: Client error occurred when submitting URL {url}: {e}")
                return None
            except Exception as e:
                logging.error(f"DOM.py: Unexpected error occurred when submitting URL {url}: {e}")
                return None

    async def get_result(self, uuid: str, retries: int):
        """
        Retrieves the scan result from urlscan.io using the provided UUID.
        
        Parameters:
        uuid (str): The UUID of the scan to retrieve results for.
        retries (int): The number of retry attempts if the result is not ready.
        
        Returns:
        dict or None: The JSON result from urlscan.io if successful; otherwise, None.
        """
        url = f"https://urlscan.io/api/v1/result/{uuid}/"
        for idx in range(retries):
            # Retrieve an available API key
            api_key = await self.api_key_manager.get_api_key()
            headers = {
                'User-Agent': self.user_agent,
                'API-Key': api_key
            }

            retry_delay = min(3**idx, 15) # Exponential backoff with a maximum delay of 15 seconds
            logging.info(f"DOM.py: Attempt {idx + 1}/{retries}: Fetching result for UUID {uuid}")
            try:
                # Make a GET request to fetch the scan result
                async with self.session.get(url, headers=headers, timeout=ClientTimeout(total=60)) as response:
                    status = response.status
                    if status == 200:
                        result = await response.json()
                        return result
                    elif status == 404:
                        # The scan result is not ready yet; wait and retry
                        await asyncio.sleep(retry_delay)
                        continue
                    elif status == 429:
                        # Rate limited; handle by marking the API key and retrying
                        reset_after = response.headers.get('X-Rate-Limit-Reset-After')
                        if reset_after is not None:
                            reset_after = int(reset_after)
                        else:
                            reset_after = 60
                            logging.warning(f"DOM.py: 'X-Rate-Limit-Reset-After' header not found. Using default wait time of {reset_after} seconds.")
                        logging.warning(f"DOM.py: Rate limited by urlscan.io when fetching result. Waiting for {reset_after} seconds.")
                        await self.api_key_manager.mark_rate_limited(api_key, reset_after)
                        continue  # Try with another API key
                    else:
                        # Unexpected status code
                        logging.error(f"DOM.py: Error fetching result for UUID {uuid}: HTTP {response.status}")
                        return None
            except aiohttp.ClientError as e:
                logging.error(f"DOM.py: Client error occurred when fetching result for UUID {uuid}: {e}")
                return None
            except asyncio.TimeoutError:
                logging.error(f"DOM.py: Request timed out when fetching result for UUID {uuid}")
                return None
        logging.error(f"DOM.py: Exceeded maximum retries ({retries}) for UUID {uuid}.")
        return None

    async def get_dom_snapshot(self, uuid: str, retries: int):
        """
        Retrieves the DOM snapshot from urlscan.io using the provided UUID.
        
        Parameters:
        uuid (str): The UUID of the scan to retrieve the DOM snapshot for.
        retries (int): The number of retry attempts if the snapshot is not ready.
        
        Returns:
        str or None: The DOM snapshot as a string if successful; otherwise, None.
        """
        url = f"https://urlscan.io/dom/{uuid}/"
        for idx in range(retries):
            # Retrieve an available API key
            api_key = await self.api_key_manager.get_api_key()
            headers = {
                'User-Agent': self.user_agent,
                'API-Key': api_key
            }

            retry_delay = min(3**idx, 15) # Exponential backoff with a maximum delay of 15 seconds
            logging.info(f"DOM.py: Attempt {idx + 1}/{retries}: Fetching DOM snapshot for UUID {uuid}")
            try:
                # Make a GET request to fetch the DOM snapshot
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
                        # Rate limited; handle by marking the API key and retrying
                        reset_after = response.headers.get('X-Rate-Limit-Reset-After')
                        if reset_after is not None:
                            reset_after = int(reset_after)
                        else:
                            reset_after = 60
                            logging.warning(f"DOM.py: 'X-Rate-Limit-Reset-After' header not found. Using default wait time of {reset_after} seconds.")
                        logging.warning(f"DOM.py: Rate limited by urlscan.io when fetching DOM snapshot. Waiting for {reset_after} seconds.")
                        await self.api_key_manager.mark_rate_limited(api_key, reset_after)
                        continue  # Try with another API key
                    else:
                        # Unexpected status code
                        logging.error(f"DOM.py: Error fetching DOM snapshot for UUID {uuid}: HTTP {response.status}")
                        return None
            except aiohttp.ClientError as e:
                logging.error(f"DOM.py: Client error occurred when fetching DOM snapshot for UUID {uuid}: {e}")
                return None
            except asyncio.TimeoutError:
                logging.error(f"DOM.py: Request timed out when fetching DOM snapshot for UUID {uuid}")
                return None
        logging.error(f"DOM.py: Exceeded maximum retries ({retries}) for UUID {uuid} when fetching DOM snapshot.")
        return None

    async def extract_dom_features(self, dom_content: str):
        """
        Extracts various DOM-related features from the provided DOM content.
        
        Parameters:
        dom_content (str): The HTML content of the DOM snapshot.
        
        Updates:
        self.feat_dict (dict): Updates the feature dictionary with extracted DOM features.
        """
        # Parse the DOM content using BeautifulSoup in a separate thread to avoid blocking the event loop
        soup = await asyncio.to_thread(BeautifulSoup, dom_content, 'html.parser')

        # Extract DOM features
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
        """
        Calculates the total number of nodes in the DOM.
        """
        return len(soup.find_all())

    def get_max_depth(self, soup):
        """
        Calculates the maximum depth of the DOM tree.
        """
        def helper(node, current_depth=0):
            if not hasattr(node, 'contents') or not node.contents:
                return current_depth
            else:
                return max(helper(child, current_depth + 1) for child in node.contents if hasattr(child, 'name'))
        return helper(soup)

    def get_average_depth(self, soup):
        """
        Calculates the average depth of the DOM tree.
        """
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
        """
        Counts the number of unique HTML tags used in the DOM.
        """
        tags = {tag.name for tag in soup.find_all()}
        return len(tags)

    def get_num_comments(self, soup):
        """
        Counts the number of HTML comments in the DOM.
        """
        comments = soup.find_all(string=lambda text: isinstance(text, type(soup.comment)))
        return len(comments)

    def has_element(self, soup, tag_name):
        """
        Checks if a specific HTML element is present in the DOM.
        """
        return 1 if soup.find(tag_name) else 0

    def get_total_attributes(self, soup):
        """
        Calculates the total number of attributes across all HTML tags in the DOM.
        """
        return sum(len(tag.attrs) for tag in soup.find_all())

    def get_average_attributes(self, soup):
        """
        Calculates the average number of attributes per HTML tag in the DOM.
        """
        total_attributes = self.get_total_attributes(soup)
        total_elements = len(soup.find_all())
        return total_attributes / total_elements if total_elements else 0

    def get_inline_event_handlers(self, soup):
        """
        Counts the number of inline event handlers in the DOM.
        """
        inline_events = ['onload', 'onerror', 'onclick', 'onmouseover', 'onmouseout', 'onkeydown', 'onkeyup']
        return sum(
            1 for tag in soup.find_all() for attr in inline_events if attr in tag.attrs
        )

    def get_deprecated_tags_used(self, soup):
        """
        Counts the number of deprecated HTML tags used in the DOM.
        """
        deprecated_tags = ['applet', 'basefont', 'center', 'dir', 'font', 'frame', 'frameset',
                           'isindex', 'menu', 'noframes', 's', 'strike', 'u']
        return sum(1 for tag in deprecated_tags if soup.find(tag))

    async def extract(self, url: str):
        """
        Orchestrates the extraction of DOM-related features from the specified URL.
        
        Parameters:
        url (str): The URL from which to extract DOM features.
        
        Returns:
        dict: A dictionary containing the extracted DOM features.
        """
        # Initialize the feature dictionary with default values
        self.initialize_feat_dict(url)
        # Submit the URL for scanning and retrieve the UUID
        uuid = await self.submit_url(url)
        if uuid is None:
            logging.error(f"DOM.py: Failed to submit URL: {url}")
            return self.feat_dict

        logging.info(f"DOM.py: Submitted URL: {url}, UUID: {uuid}")
        # Wait for 10 seconds before attempting to fetch the result
        await asyncio.sleep(10)

        # Retrieve the scan result using the UUID
        result = await self.get_result(uuid, retries=5)
        if result is None:
            logging.error(f"DOM.py: No result obtained for UUID {uuid}")
            return self.feat_dict

        # Retrieve the DOM snapshot using the UUID
        dom_content = await self.get_dom_snapshot(uuid, retries=5)
        if dom_content is None:
            logging.error(f"DOM.py: No DOM content obtained for UUID {uuid}")
            return self.feat_dict

        # Extract DOM features from the DOM content
        await self.extract_dom_features(dom_content)

        # Add the screenshot URL to the feature dictionary
        self.feat_dict['dom_screenshot_url'] = f"https://urlscan.io/screenshots/{uuid}.png"

        logging.info(f'DOM.py: Successfully returned DOM features for url: {url}')
        return self.feat_dict