import whois
import tldextract
from typing import Union

class Domain:
    def __init__(self, urls: list) -> None:
        self.urls = urls
        self.feat_dict = {}

    @staticmethod
    def get_domain(w: whois.WhoisEntry) -> Union[list, str]:
        return w.domain_name

    @staticmethod
    def get_domain_length(w: whois.WhoisEntry) -> Union[list, str]:
        return len(w.domain_name)
    
    @staticmethod
    def get_name_servers(w: whois.WhoisEntry) -> Union[list, str]:
        return w.name_servers

    @staticmethod
    def get_TLD(w) -> str:
        domain = w.domain_name
        if isinstance(domain, list):
            domain = domain[0]
        extracted = tldextract.extract(domain)
        return extracted.suffix

    @staticmethod
    def get_registrar(w: whois.WhoisEntry) -> Union[list, str]:
        return w.registrar

    @staticmethod
    def get_whois_server(w: whois.WhoisEntry) -> Union[list, str]:
        return w.whois_server

    @staticmethod
    def get_creation_date(w: whois.WhoisEntry) -> Union[list, str]:
        return w.creation_date
    
    @staticmethod
    def get_expiration_date(w: whois.WhoisEntry) -> Union[list, str]:
        return w.expiration_date

    @staticmethod
    def get_updated_date(w: whois.WhoisEntry) -> Union[list, str]:
        return w.updated_date

    @staticmethod
    def get_dnssec(w: whois.WhoisEntry) -> Union[list, str]:
        return w.dnssec
    
    def extract(self) -> list:
        for url in self.urls:
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
                return

example = Domain(['https://www.google.com'])
example.extract()
print(example.feat_dict)