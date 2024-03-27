import whois
import tldextract
from typing import Union

class Domain:
    def __init__(self) -> None:
        self.feat_dict = {}

    @staticmethod
    def get_domain(w: whois.WhoisEntry) -> Union[int, str]:
        try:
            return w.domain_name
        except:
            return -1

    @staticmethod
    def get_domain_length(w: whois.WhoisEntry) -> Union[int, str]:
        try:
            return len(w.domain_name)
        except:
            return -1
    
    @staticmethod
    def get_name_servers(w: whois.WhoisEntry) -> Union[int, str]:
        try:
            return ', '.join([str(item) for item in w.name_servers])
        except:
            return -1

    @staticmethod
    def get_TLD(w) -> str:
        try:
            domain = w.domain_name
            if isinstance(domain, list):
                domain = domain[0]
            extracted = tldextract.extract(domain)
            return extracted.suffix
        except:
            return -1

    @staticmethod
    def get_registrar(w: whois.WhoisEntry) -> Union[int, str]:
        try:
            return w.registrar
        except:
            return -1

    @staticmethod
    def get_whois_server(w: whois.WhoisEntry) -> Union[int, str]:
        try:
            return w.whois_server
        except:
            return -1

    @staticmethod
    def get_creation_date(w: whois.WhoisEntry) -> Union[int, str]:
        try:
            return w.creation_date.strftime("%m/%d/%Y, %H:%M:%S")
        except:
            return -1
    
    @staticmethod
    def get_expiration_date(w: whois.WhoisEntry) -> Union[int, str]:
        try:
            return w.expiration_date.strftime("%m/%d/%Y, %H:%M:%S")
        except:
            return -1

    @staticmethod
    def get_updated_date(w: whois.WhoisEntry) -> Union[int, str]:
        try:
            return '| '.join([item.strftime("%m/%d/%Y, %H:%M:%S") for item in w.updated_date])
        except:
            return -1

    @staticmethod
    def get_dnssec(w: whois.WhoisEntry) -> Union[int, str]:
        try:
            return w.dnssec
        except:
            return -1
    
    def extract(self, url):
        self.feat_dict['url'] = url

        try:
            w = whois.whois(url)
            self.feat_dict['domain'] = Domain.get_domain(w)
            self.feat_dict['domain_length'] = Domain.get_domain_length(w)
            self.feat_dict['name_servers'] = Domain.get_name_servers(w)
            self.feat_dict['TLD'] = Domain.get_TLD(w)
            self.feat_dict['registrar'] = Domain.get_registrar(w)
            self.feat_dict['whois_server'] = Domain.get_whois_server(w)
            self.feat_dict['creation_date'] = Domain.get_creation_date(w)
            self.feat_dict['expiration_date'] = Domain.get_expiration_date(w)
            self.feat_dict['updated_date'] = Domain.get_updated_date(w)
            self.feat_dict['dnssec'] = Domain.get_dnssec(w)

        except Exception as e:
            print(f'Error making request: {e}')
            return {}
        
        return self.feat_dict

# example = Domain()
# print(example.extract('https://www.southbankmosaics.com/'))

# for keys in example.feat_dict:
#     print(keys + " " + str(type(example.feat_dict[keys])))
#     print(example.feat_dict[keys])
#     print()