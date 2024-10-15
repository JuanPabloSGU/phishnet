import sys
import os
import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from utilities.ServiceUtils import generate_user_agent

logging.basicConfig(level=logging.INFO)

class Content:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session
        self.user_agent = generate_user_agent()
        self.headers = {
            'User-Agent': self.user_agent,
            'Connection': 'close'
        }
        self.feat_dict = {}

    def initialize_feat_dict(self, url):
        self.feat_dict = {'url': url}
        feature_names = [
            'content_redirects',
            'content_len_html',
            'content_len_text',
            'content_len_links',
            'content_len_mail_usage_forms',
            'content_meta_script_link_percentage',
            'content_mouseover_changes',
            'content_right_click_disabled',
            'content_keyboard_shortcuts_disabled',
            'content_copy_paste_disabled',
            'content_drag_drop_disabled',
            'content_popup_window_has_text_field',
            'content_use_iframe',
            'content_use_upload',
            'content_use_download',
            'content_use_http_link'
        ]
        for feature in feature_names:
            self.feat_dict[feature] = -1 if feature != 'content_meta_script_link_percentage' else '-1'

    async def make_request(self, url: str, timeout: int, retries: int):
        for idx in range(retries):
            try:
                async with self.session.get(url, timeout=timeout, allow_redirects=True) as response:
                    response.raise_for_status()
                    content = await response.read()
                    redirects = len(response.history)
                    return {'content': content, 'redirects': redirects}
            except aiohttp.ClientError:
                retry_delay = 2**idx
                logging.error(f'Content.py: ClientError for {url}. Retrying in {retry_delay} seconds.')
                await asyncio.sleep(retry_delay)
            except Exception:
                logging.error(f'Content.py: Error making request for url: {url}')
                return None
        logging.error(f'Content.py: Failed to make request after {retries} retries.')
        return None
    
    def get_links(self, soup: BeautifulSoup) -> int:
        """
        Return the number of links in a given HTML soup.
        """
        try:
            return len(soup.find_all('a'))
        except:
            return -1

    def get_mail_usage_form(self, soup: BeautifulSoup) -> int:
        """
        Return the number of mailto links in a given HTML soup.
        Returns 1 if mailto or mail links are found, 0 otherwise.
        """
        try:
            forms = soup.find_all('form')
            for form in forms:
                if 'mail(' in str(form) or 'mailto:' in str(form):
                    return 1
            return 0
        except:
            return -1

    def meta_script_link_percentage(self, soup: BeautifulSoup) -> tuple[float, float, float]:
        """
        Returns the percentage of meta, script, and link tags.
        """
        try:
            meta = soup.find_all('meta')
            script = soup.find_all('script')
            link_tags = soup.find_all('link')

            meta_links = sum([1 for tag in meta if tag.has_attr('href')])
            script_links = sum([1 for tag in script if tag.has_attr('src')])
            link_links = sum([1 for tag in link_tags if tag.has_attr('href')])

            total_links = meta_links + script_links + link_links
            if total_links == 0:
                return "0, 0, 0"
            
            meta_percentage = meta_links / total_links
            script_percentage = script_links / total_links
            link_percentage = link_links / total_links

            return str(meta_percentage) + ", " + str(script_percentage) + ", " + str(link_percentage)
        except:
            return "-1, -1, -1"

    def get_mouseover_changes(self, soup: BeautifulSoup) -> int:
        """
        Returns if mouseover events change the status bar (1), otherwise 0.
        """
        try:
            onMouseOver_tags = soup.find_all(onmouseover=True)
            for tag in onMouseOver_tags:
                if 'window.status' in str(tag):
                    return 1
            return 0
        except:
            return -1

    def get_right_click_disabled(self, soup: BeautifulSoup) -> int:
        """
        Returns if right click is disabled (1), otherwize 0.
        """
        try:
            for tag in soup.find_all('script'):
                if 'event.button==2' in tag.text:
                    return 1
            return 0
        except:
            return -1

    def get_keyboard_shortcuts_disabled(self, soup: BeautifulSoup) -> int:
        """
        Return if keyboard shortcuts are disabled (1), otherwise 0.
        """
        try:
            for tag in soup.find_all('script'):
                if 'event.preventDefault()' in tag.text:
                    return 1
            return 0
        except:
            return -1

    def get_copy_paste_disabled(self, soup: BeautifulSoup) -> int:
        """
        Return if copy-paste is disabled (1), otherwise 0.
        """
        try:
            for tag in soup.find_all('script'):
                if 'event.clipboardData' in tag.text or 'event.preventDefault()' in tag.text:
                    return 1
            return 0
        except:
            return -1

    def get_drag_drop_disabled(self, soup: BeautifulSoup) -> int:
        """
        Return if drag and drop is disabled (1), otherwise 0.
        """
        try:
            for tag in soup.find_all('script'):
                if 'event.dataTransfer' in tag.text or 'event.preventDefault()' in tag.text:
                    return 1
            return 0
        except:
            return -1

    def popup_window_has_text_field(self, soup: BeautifulSoup) -> int:
        """
        Return if a popup window has a text field (1), otherwise 0.
        """
        try:
            popups = soup.find_all('div', {'class': 'popup'})
            for popup in popups:
                if popup.find('input', {'type': 'text'}):
                    return 1
            return 0
        except:
            return -1

    def use_iframe(self, soup: BeautifulSoup) -> int:
        """
        Return if an iframe is used (1), otherwise 0.
        """
        try:
            iframes = soup.find_all('iframe')
            if len(iframes) > 0:
                return 1
            return 0
        except:
            return -1

    def use_upload(self, soup: BeautifulSoup) -> int:
        """
        Return if an upoload is present (1), otherwise 0.
        """
        try:
            upload = soup.find_all('input', type="file")
            if len(upload) > 0:
                return 1
            return 0
        except:
            return -1
    
    def use_download(self, soup: BeautifulSoup) -> int:
        """
        Return if an download is present (1), otherwise 0.
        """
        try:
            all_links = soup.find_all('a')

            for link in all_links:
                href = link.get('href')
                if href:
                    if 'download' in href.lower():
                        return 1
            return 0
        except:
            return -1

    def use_http_link(self, soup: BeautifulSoup) -> int:
        """
        Return if a http link is present in the http
        """
        try:
            all_links = soup.find_all('a')
            for link in all_links:
                href = link.get('href')
                if href:
                    if 'http:' in href.lower():
                        return 1
            return 0
        except:
            return -1


    async def extract(self, url):
        self.initialize_feat_dict(url)

        try:
            response_data = await self.make_request(url, timeout=15, retries=3)
            if response_data is None:
                return self.feat_dict
            self.feat_dict['content_redirects'] = response_data['redirects']
        except Exception:
            print(f'Content.py: Error making request')
            return self.feat_dict

        try:
            content = response_data['content']
            soup = BeautifulSoup(content, 'html.parser')
            self.feat_dict['content_len_html'] = len(soup.prettify())
            self.feat_dict['content_len_text'] = len(soup.get_text())
            self.feat_dict['content_len_links'] = self.get_links(soup)
            self.feat_dict['content_len_mail_usage_forms'] = self.get_mail_usage_form(soup)
            self.feat_dict['content_meta_script_link_percentage'] = self.meta_script_link_percentage(soup)
            self.feat_dict['content_mouseover_changes'] = self.get_mouseover_changes(soup)
            self.feat_dict['content_right_click_disabled'] = self.get_right_click_disabled(soup)
            self.feat_dict['content_keyboard_shortcuts_disabled'] = self.get_keyboard_shortcuts_disabled(soup)
            self.feat_dict['content_copy_paste_disabled'] = self.get_copy_paste_disabled(soup)
            self.feat_dict['content_drag_drop_disabled'] = self.get_drag_drop_disabled(soup)
            self.feat_dict['content_popup_window_has_text_field'] = self.popup_window_has_text_field(soup)
            self.feat_dict['content_use_iframe'] = self.use_iframe(soup)
            self.feat_dict['content_use_upload'] = self.use_upload(soup)
            self.feat_dict['content_use_download'] = self.use_download(soup)
            self.feat_dict['content_use_http_link'] = self.use_http_link(soup)

        except Exception:
            logging.error(f'Content.py: Error parsing HTML for url: {url}')
            return self.feat_dict
        
        logging.info(f'Content.py: Successfully returned Content features for url: {url}')
        return self.feat_dict

# For testing purposes
# async def run_example():
#     async with aiohttp.ClientSession() as session:
#         example = Content(session)
#         await example.extract('https://afmeldeninfo.com/unsubs-be-nee')
        
#         for key, value in example.feat_dict.items():
#             print(f"{key}: {type(value)}")
#             print(value)

# asyncio.run(run_example())