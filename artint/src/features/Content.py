import random
from bs4 import BeautifulSoup
import requests
import time

def generate_user_agent(self) -> str:
    """
    Generate a random user agent.
    """
    a = random.randint(63, 89)
    b = random.randint(1, 3200)
    c = random.randint(1, 140)
    user_agent = f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{a}.0.{b}.{c} Safari/537.36'
    return user_agent

class Content:
    def __init__(self, urls: list) -> None:
        self.urls = urls
        self.user_agent = generate_user_agent(self)
        self.headers = {}
        self.headers['User-Agent'] = self.user_agent
        self.feat_dict = {}
    
    def make_request(self, url: str, timeout: int, retries: int) -> requests.Response:
        for idx in range(retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=timeout, allow_redirects=True)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                retry_delay = 2**idx
                print(f'\033[34mRequestException for {url}. Retrying in {retry_delay} seconds.\033[0m')
                time.sleep(retry_delay)
            except Exception as e:
                print(f'\033[31mError making request for {url}: {e}\033[0m')
                return None
        print(f'\033[31mFailed to make request after {retries} retries.\033[0m')
        return None

    def redirects(self, response: requests.Response) -> int:
        """
        Return the number of redirects in a given response.
        """
        try:
            return len(response.history)
        except:
            return -1
    
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
            return 0

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
            return -1

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


    def extract(self):

        for url in self.urls:
            self.feat_dict['url'] = url

            try:
                response = self.make_request(url, timeout=5, retries=3)
                if response is None:
                    return
                self.feat_dict['redirects'] = self.redirects(response)
            except Exception as e:
                print(f'Error making request: {e}')
                return

            try:
                soup = BeautifulSoup(response.content, 'html.parser')
                self.feat_dict['len_html'] = len(soup.prettify())
                self.feat_dict['len_text'] = len(soup.get_text())
                self.feat_dict['len_links'] = self.get_links(soup)
                self.feat_dict['len_mail_usage_forms'] = self.get_mail_usage_form(soup)
                self.feat_dict['meta_script_link_percentage'] = self.meta_script_link_percentage(soup)
                self.feat_dict['mouseover_changes'] = self.get_mouseover_changes(soup)
                self.feat_dict['right_click_disabled'] = self.get_right_click_disabled(soup)
                self.feat_dict['keyboard_shortcuts_disabled'] = self.get_keyboard_shortcuts_disabled(soup)
                self.feat_dict['copy_paste_disabled'] = self.get_copy_paste_disabled(soup)
                self.feat_dict['drag_drop_disabled'] = self.get_drag_drop_disabled(soup)
                self.feat_dict['popup_window_has_text_field'] = self.popup_window_has_text_field(soup)
                self.feat_dict['use_iframe'] = self.use_iframe(soup)
                self.feat_dict['use_upload'] = self.use_upload(soup)
                self.feat_dict['use_download'] = self.use_download(soup)
                self.feat_dict['use_http_link'] = self.use_http_link(soup)

            except Exception as e:
                print(f'Error parsing HTML: {e}')
                return

# example = Content(['https://www.google.com/search?q=dlak&sca_esv=5bdde8b43c3acd18&sca_upv=1&sxsrf=ACQVn0-kYdzzhYGRYlS3Vyp5NMnK3wKCrA%3A1708971628303&source=hp&ei=bNbcZaSMEPfdkPIPjci9mAI&iflsig=ANes7DEAAAAAZdzkfJkItMmjQG1EFyfk2IUnQ4wYw_0D&ved=0ahUKEwik8tW2z8mEAxX3LkQIHQ1kDyMQ4dUDCBc&uact=5&oq=dlak&gs_lp=Egdnd3Mtd2l6IgRkbGFrMgUQABiABDIFEAAYgAQyBRAAGIAEMgoQABiABBgKGLEDMgoQABiABBgKGLEDMg0QLhiABBgKGMcBGK8BMg0QABiABBgKGLEDGIMBMgoQABiABBgKGLEDMg0QABiABBgKGLEDGIMBMgcQABiABBgKSNwCUABYrQFwAHgAkAEAmAGpAaABtgSqAQMwLjS4AQPIAQD4AQGYAgSgAvIEwgIEECMYJ8ICChAjGIAEGIoFGCfCAgsQABiABBixAxiDAcICERAuGIAEGLEDGIMBGMcBGNEDwgIREC4YgwEY1AIYsQMYgAQYigXCAggQABiABBixA8ICERAuGIMBGK8BGMcBGLEDGIAEwgILEC4YgAQYxwEYrwHCAg0QLhiABBjHARjRAxgKmAMAkgcDMC40&sclient=gws-wiz'])
# example.extract()
# print(example.feat_dict)

# for keys in example.feat_dict:
#     print(keys + " " + str(type(example.feat_dict[keys])))
#     print(example.feat_dict[keys])
#     print()