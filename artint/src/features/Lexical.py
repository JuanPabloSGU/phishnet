from collections import Counter
from urllib.parse import urlparse
from math import log2
import re
from ipaddress import ip_address

# feature overlap can cause false positive since higher weight

class Lexical: 

    def __init__(self, urls: list) -> None:
        self.urls = urls
        self.feat_dict = {}

    def extract(self) -> list: 

        for url in self.urls:
            scheme, netloc, path, params, query, fragment = urlparse(url)

            self.feat_dict[f'url'] = url
            self.feat_dict['len_url'] = len(url)

            for component in [netloc, path]:
                name = f'{component=}'.partition('=')[0]

                self.feat_dict[f'len_{name}'] = len(component)
                self.feat_dict[f'count_digits_{name}'] = Lexical.count_digits(component)
                self.feat_dict[f'count_letters_{name}'] = Lexical.count_letters(component)
                self.feat_dict[f'ratio_digits_{name}_url'] = Lexical.component_ratio(self.feat_dict[f'count_digits_{name}'], url)
                self.feat_dict[f'ratio_letters_{name}_url'] = Lexical.component_ratio(self.feat_dict[f'count_letters_{name}'], url)
        
            self.feat_dict['count_dots_url'] = Lexical.count_sub(url, '.')
            self.feat_dict['count_percent_url'] = Lexical.count_sub(url, '%')
            self.feat_dict['count_hash_url'] = Lexical.count_sub(url, '#')
            self.feat_dict['count_ats_url'] = Lexical.count_sub(url, '@')
            self.feat_dict['count_embed_url'] = Lexical.count_sub(url, '//')

            self.feat_dict['use_https'] = Lexical.uses_https(scheme)
            self.feat_dict['no_of_directories'] = Lexical.no_of_directories(path)
            self.feat_dict['contains_ip_address'] = Lexical.contains_ip_address(netloc)
            self.feat_dict['character_continuity_rate_url'] = Lexical.character_continuity_rate(url)

            self.feat_dict['shannon_entropy_url'] = Lexical.shannon_entropy(url)


    @staticmethod
    def component_ratio(one, two):
        p = len(one) if type(one) is str else one
        q = len(two) if type(two) is str else two

        if not(p and q):
            return 0
        return p / q

    @staticmethod
    def count_digits(_str: str):
        return sum(c.isdigit() for c in _str)

    @staticmethod
    def count_letters(_str: str):
        return sum(c.isalpha() for c in _str)
    
    @staticmethod
    def uses_https(scheme: str):
        """Check if a given URL scheme is HTTPS."""
        return scheme == 'https'

    @staticmethod
    def shannon_entropy(url: str):
        """Calculate the Shannon entropy of a URL. Used to catch URLs with high randomness."""
        prob = [float(url.count(c)) / len(url) for c in dict.fromkeys(list(url))]
        return - sum([p * log2(p) for p in prob])
    
    @staticmethod
    def relative_entropy(url: str):
        """Calculate the relative entropy of a URL. Used to compare against a baseline of known legitimate URLs."""
        pass

    @staticmethod
    def alphabet_entropy(netloc):
        """Calculate the entropy of the domain based on its alphabetic characters."""
        # Extract the domain name and focus only on alphabetic characters
        domain = netloc.split(':')[0]  # Remove port number if present
        alphabet = re.sub(r'[^a-zA-Z]', '', domain)  # Keep only alphabetic characters
        alphabet_freq = Counter(alphabet) # Frequency of each alphabetic character
        total_chars = len(alphabet)
        return -sum((count / total_chars) * log2(count / total_chars) for count in alphabet_freq.values() if count > 0)
    
    @staticmethod
    def count_sub(_str: str, _sub: str):
        """Count occurences of substring in string"""
        return _str.count(_sub)
    
    @staticmethod
    def no_of_directories(path: str):
        """Count the number of directories in the URL path."""
        return len(path.split('/')) - 1
    
    @staticmethod
    def contains_ip_address(netloc: str):
        """Check if netloc of URL contains an IP"""
        netloc = netloc.split(':')[0] # remove port number if present
        try:
            ip_address(netloc)
            r = 1
        except ValueError:
            r = 0
        finally:
            return r

    @staticmethod
    def character_continuity_rate(url: str):
        """Calculate the Character Continuity Rate (CCR) of a URL."""
        consecutive_chars = re.findall(r'(.)\1+', url) # Find all consecutive characters
        total_consecutive_length = sum(len(match) for match in consecutive_chars) # Count the total length of all consecutive characters
        return 0 if len(url) == 0 else total_consecutive_length / len(url)
    