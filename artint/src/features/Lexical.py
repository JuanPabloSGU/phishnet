from collections import Counter
from urllib.parse import urlparse
from math import log2
import re
from ipaddress import ip_address
import logging

logging.basicConfig(level=logging.INFO)

class Lexical: 
    """
    A class to extract various lexical features from a given URL.
    
    This class handles parsing the URL, analyzing its components, and extracting
    features related to the length, composition, and entropy of different parts of the URL.
    """

    def __init__(self) -> None:
        """
        Initializes the Lexical extractor by setting up the feature dictionary.
        """
        self.feat_dict = {}
    
    def initialize_feat_dict(self, url):
        """
        Initializes the feature dictionary with default values for a given URL.
        
        Parameters:
        url (str): The URL for which lexical features are being extracted.
        """
        self.feat_dict = {'url': url}
        feature_names = [
            'lexical_len_url',
            'lexical_len_netloc',
            'lexical_len_path',
            'lexical_count_digits_netloc',
            'lexical_count_digits_path',
            'lexical_count_letters_netloc',
            'lexical_count_letters_path',
            'lexical_ratio_digits_netloc_url',
            'lexical_ratio_digits_path_url',
            'lexical_ratio_letters_netloc_url',
            'lexical_ratio_letters_path_url',
            'lexical_count_dots_url',
            'lexical_count_percent_url',
            'lexical_count_hash_url',
            'lexical_count_ats_url',
            'lexical_count_embed_url',
            'lexical_use_https',
            'lexical_no_of_directories',
            'lexical_contains_ip_address',
            'lexical_character_continuity_rate_url',
            'lexical_shannon_entropy_url'
        ]
        # Initialize the feature dictionary with default values and the URL
        for feature in feature_names:
            self.feat_dict[feature] = -1

    def extract(self, url):
        """
        Extracts all defined lexical features from the specified URL.

        Parameters:
        url (str): The URL from which to extract lexical features.
        
        Returns:
        dict: A dictionary containing the extracted lexical features.
        """
        # Initialize the feature dictionary with default values and the URL
        self.initialize_feat_dict(url)
        try:
            # Parse the URL into its components
            scheme, netloc, path, params, query, fragment = urlparse(url)
            # Store the length of the full URL
            self.feat_dict['lexical_len_url'] = len(url)

            # Iterate over 'netloc' and 'path' components to extract features
            for name, component in {'netloc': netloc, 'path': path}.items():
                self.feat_dict[f'lexical_len_{name}'] = len(component)
                self.feat_dict[f'lexical_count_digits_{name}'] = Lexical.count_digits(component)
                self.feat_dict[f'lexical_count_letters_{name}'] = Lexical.count_letters(component)
                self.feat_dict[f'lexical_ratio_digits_{name}_url'] = Lexical.component_ratio(self.feat_dict[f'lexical_count_digits_{name}'], url)
                self.feat_dict[f'lexical_ratio_letters_{name}_url'] = Lexical.component_ratio(self.feat_dict[f'lexical_count_letters_{name}'], url)

            # Count specific substrings within the full URL
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

            logging.info(f'Lexical.py: Successfully returned lexical features for url: {url}')
            return self.feat_dict
        except Exception:
            logging.error(f'Lexical.py: Error extracting lexical features for url: {url}')
            return self.feat_dict

    @staticmethod # helper method for computing the ratio between 2 components (either int or str); e.g., ratio between netloc and url. 
    def component_ratio(one, two):
        try:
            p = len(one) if type(one) is str else one
            q = len(two) if type(two) is str else two

            if not(p and q):
                return 0
            return p / q
        except:
            return -1

    @staticmethod # count number of digits in string
    def count_digits(_str: str):
        try:
            return sum(c.isdigit() for c in _str)
        except:
            return -1

    @staticmethod # count number of alphanumeric characters in string
    def count_letters(_str: str):
        try:
            return sum(c.isalpha() for c in _str)
        except:
            return -1
    
    @staticmethod
    def uses_https(scheme: str):
        """Check if a given URL scheme is HTTPS."""
        try:
            return 1 if scheme == 'https' else 0
        except:
            return -1

    @staticmethod
    def shannon_entropy(url: str):
        """Calculate the Shannon entropy of a URL. Used to catch URLs with high randomness."""
        try:
            prob = [float(url.count(c)) / len(url) for c in dict.fromkeys(list(url))]
            return - sum([p * log2(p) for p in prob])
        except:
            return -1
    
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
            return -1

    @staticmethod
    def count_sub(_str: str, _sub: str):
        """Count occurences of substring in string"""
        try:
            return _str.count(_sub)
        except:
            return -1
    
    @staticmethod
    def no_of_directories(path: str):
        """Count the number of directories in the URL path."""
        try:
            return len(path.split('/')) - 1
        except:
            return -1
    
    @staticmethod
    def contains_ip_address(netloc: str):
        """Check if netloc of URL contains an IP"""
        try:
            netloc = netloc.split(':')[0]  # Remove port number if present
            ip_address(netloc)
            return 1
        except ValueError:
            return 0
        except:
            return -1

    @staticmethod
    def character_continuity_rate(url: str):
        """Calculate the Character Continuity Rate (CCR) of a URL."""
        try:
            consecutive_chars = re.findall(r'(.)\1+', url) # Find all consecutive characters
            total_consecutive_length = sum(len(match) for match in consecutive_chars) # Count the total length of all consecutive characters
            return 0 if len(url) == 0 else total_consecutive_length / len(url)
        except:
            return -1


# example = Lexical()
# print(example.extract('https://www.google.com'))

# for keys in example.feat_dict:
#     print(keys + " " + str(type(example.feat_dict[keys])))
#     print(example.feat_dict[keys])
#     print()