from collections import Counter
from urllib.parse import urlparse
from math import log2
import re
from ipaddress import ip_address

# feature overlap can cause false positive since higher weight

class Lexical: 

    def __init__(self) -> None:
        self.feat_dict = {}

    def extract(self, url): 
        scheme, netloc, path, params, query, fragment = urlparse(url)

        self.feat_dict['url'] = url
        self.feat_dict['lexical_len_url'] = len(url)

        for name, component in {'netloc': netloc, 'path': path}.items():
            self.feat_dict[f'lexical_len_{name}'] = len(component)
            self.feat_dict[f'lexical_count_digits_{name}'] = Lexical.count_digits(component)
            self.feat_dict[f'lexical_count_letters_{name}'] = Lexical.count_letters(component)
            self.feat_dict[f'lexical_ratio_digits_{name}_url'] = Lexical.component_ratio(self.feat_dict[f'lexical_count_digits_{name}'], url)
            self.feat_dict[f'lexical_ratio_letters_{name}_url'] = Lexical.component_ratio(self.feat_dict[f'lexical_count_letters_{name}'], url)

        self.feat_dict['lexical_count_dots_url'] = Lexical.count_sub(url, '.')
        self.feat_dict['lexical_count_percent_url'] = Lexical.count_sub(url, '%')
        self.feat_dict['lexical_count_hash_url'] = Lexical.count_sub(url, '#')
        self.feat_dict['lexical_count_ats_url'] = Lexical.count_sub(url, '@')
        self.feat_dict['lexical_count_embed_url'] = Lexical.count_sub(url, '//')

        self.feat_dict['lexical_use_https'] = Lexical.uses_https(scheme)
        self.feat_dict['lexical_no_of_directories'] = Lexical.no_of_directories(path)
        self.feat_dict['lexical_contains_ip_address'] = Lexical.contains_ip_address(netloc)
        self.feat_dict['lexical_character_continuity_rate_url'] = Lexical.character_continuity_rate(url)

        self.feat_dict['lexical_shannon_entropy_url'] = Lexical.shannon_entropy(url)

        return self.feat_dict

    @staticmethod
    def component_ratio(one, two):
        try:
            p = len(one) if type(one) is str else one
            q = len(two) if type(two) is str else two

            if not(p and q):
                return 0
            return p / q
        except:
            return None

    @staticmethod
    def count_digits(_str: str):
        try:
            return sum(c.isdigit() for c in _str)
        except:
            return None

    @staticmethod
    def count_letters(_str: str):
        try:
            return sum(c.isalpha() for c in _str)
        except:
            return None
    
    @staticmethod
    def uses_https(scheme: str):
        """Check if a given URL scheme is HTTPS."""
        try:
            return 1 if scheme == 'https' else 0
        except:
            return None

    @staticmethod
    def shannon_entropy(url: str):
        """Calculate the Shannon entropy of a URL. Used to catch URLs with high randomness."""
        try:
            prob = [float(url.count(c)) / len(url) for c in dict.fromkeys(list(url))]
            return - sum([p * log2(p) for p in prob])
        except:
            return None
    
    @staticmethod
    def relative_entropy(url: str):
        """Calculate the relative entropy of a URL. Used to compare against a baseline of known legitimate URLs."""
        pass

    @staticmethod
    def alphabet_entropy(netloc):
        """Calculate the entropy of the domain based on its alphabetic characters."""
        try:
        # Extract the domain name and focus only on alphabetic characters
            domain = netloc.split(':')[0]  # Remove port number if present
            alphabet = re.sub(r'[^a-zA-Z]', '', domain)  # Keep only alphabetic characters
            alphabet_freq = Counter(alphabet) # Frequency of each alphabetic character
            total_chars = len(alphabet)
            return -sum((count / total_chars) * log2(count / total_chars) for count in alphabet_freq.values() if count > 0)
        except:
            return None

    @staticmethod
    def count_sub(_str: str, _sub: str):
        """Count occurences of substring in string"""
        try:
            return _str.count(_sub)
        except:
            return None
    
    @staticmethod
    def no_of_directories(path: str):
        """Count the number of directories in the URL path."""
        try:
            return len(path.split('/')) - 1
        except:
            return None
    
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
        try:
            consecutive_chars = re.findall(r'(.)\1+', url) # Find all consecutive characters
            total_consecutive_length = sum(len(match) for match in consecutive_chars) # Count the total length of all consecutive characters
            return 0 if len(url) == 0 else total_consecutive_length / len(url)
        except:
            return None


# example = Lexical()
# print(example.extract('https://www.google.com'))

# for keys in example.feat_dict:
#     print(keys + " " + str(type(example.feat_dict[keys])))
#     print(example.feat_dict[keys])
#     print()