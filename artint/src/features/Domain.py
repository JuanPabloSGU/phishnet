import whois
import tldextract
import logging
import dns.resolver
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)

class Domain:
    def __init__(self) -> None:
        self.feat_dict = {}

    def initialize_feat_dict(self, url: str) -> None:
        default_values = {
            'domain': "-1",
            'domain_length': -1,
            'domain_name_servers': "-1",
            'domain_TLD': "-1",
            'domain_registrar': "-1",
            'domain_whois_server': "-1",
            'domain_creation_date': "-1",
            'domain_expiration_date': "-1",
            'domain_updated_date': "-1",
            'domain_dnssec': "-1",
            'domain_a_record': "-1",
            'domain_aaaa_record': "-1",
            'domain_mx_record': "-1",
            'domain_cname_record': "-1",
            'domain_ns_record': "-1"
        }
        self.feat_dict = {**default_values, 'url': url}

    @staticmethod
    def get_name_servers(w: whois.WhoisEntry) -> str:
        try:
            return ', '.join([str(item) for item in w.name_servers])
        except:
            return "-1"

    @staticmethod
    def get_TLD(w) -> str:
        try:
            domain = w.domain_name
            if isinstance(domain, list):
                domain = domain[0]
            extracted = tldextract.extract(domain)
            return extracted.suffix
        except:
            return "-1"

    @staticmethod
    def get_registrar(w: whois.WhoisEntry) -> str:
        try:
            return w.registrar
        except:
            return "-1"

    @staticmethod
    def get_whois_server(w: whois.WhoisEntry) -> str:
        try:
            return w.whois_server
        except:
            return "-1"

    @staticmethod
    def get_creation_date(w: whois.WhoisEntry) -> str:
        try:
            return w.creation_date.strftime("%m/%d/%Y, %H:%M:%S")
        except:
            return "-1"
    
    @staticmethod
    def get_expiration_date(w: whois.WhoisEntry) -> str:
        try:
            return w.expiration_date.strftime("%m/%d/%Y, %H:%M:%S")
        except:
            return "-1"

    @staticmethod
    def get_updated_date(w: whois.WhoisEntry) -> str:
        try:
            return '| '.join([item.strftime("%m/%d/%Y, %H:%M:%S") for item in w.updated_date])
        except:
            return "-1"

    @staticmethod
    def get_dnssec(w: whois.WhoisEntry) -> str:
        try:
            return w.dnssec
        except:
            return "-1"

    @staticmethod
    def get_a_record(domain: str) -> str:
        try:
            if dns.resolver.resolve(domain, 'A') == None:
                return "-1"
            else:
                return ', '.join([str(item) for item in dns.resolver.resolve(domain, 'A')])
        except:
            return "-1"

    @staticmethod
    def get_aaaa_record(domain: str) -> str:
        try:
            if dns.resolver.resolve(domain, 'AAAA') == None:
                return "-1"
            else:
                return ', '.join([str(item) for item in dns.resolver.resolve(domain, 'AAAA')])
        except:
            return "-1"

    @staticmethod
    def get_mx_record(domain: str) -> str:
        try:
            if dns.resolver.resolve(domain, 'MX') == None:
                return "-1"
            else:
                return ', '.join([str(item) for item in dns.resolver.resolve(domain, 'MX')])
        except:
            return "-1"

    @staticmethod
    def get_cname_record(domain: str) -> str:
        try:
            if dns.resolver.resolve(domain, 'CNAME') == None:
                return "-1"
            else:
                return ', '.join([str(item) for item in dns.resolver.resolve(domain, 'CNAME')])
        except:
            return "-1"

    @staticmethod
    def get_ns_record(domain: str) -> str:
        try:
            if dns.resolver.resolve(domain, 'NS') == None:
                return "-1"
            else:
                return ', '.join([str(item) for item in dns.resolver.resolve(domain, 'NS')])
        except:
            return "-1"

    def extract(self, url):
        self.initialize_feat_dict(url)

        parsed_url = urlparse(url)
        domain_name = f"{parsed_url.hostname}" if parsed_url.hostname else url

        self.feat_dict['domain'] = domain_name
        self.feat_dict['domain_length'] = len(domain_name)

        try:
            w = whois.whois(domain_name)
            self.feat_dict['domain_name_servers'] = Domain.get_name_servers(w)
            self.feat_dict['domain_TLD'] = Domain.get_TLD(w)
            self.feat_dict['domain_registrar'] = Domain.get_registrar(w)
            self.feat_dict['domain_whois_server'] = Domain.get_whois_server(w)
            self.feat_dict['domain_creation_date'] = Domain.get_creation_date(w)
            self.feat_dict['domain_expiration_date'] = Domain.get_expiration_date(w)
            self.feat_dict['domain_updated_date'] = Domain.get_updated_date(w)
            self.feat_dict['domain_dnssec'] = Domain.get_dnssec(w)

        except Exception:
            logging.error(f'Domain.py: WHOIS lookup failed for url: {domain_name}')

        try:
            self.feat_dict['domain_a_record'] = Domain.get_a_record(domain_name)
            self.feat_dict['domain_aaaa_record'] = Domain.get_aaaa_record(domain_name)
            self.feat_dict['domain_mx_record'] = Domain.get_mx_record(domain_name)
            self.feat_dict['domain_cname_record'] = Domain.get_cname_record(domain_name)
            self.feat_dict['domain_ns_record'] = Domain.get_ns_record(domain_name)
        except Exception:
            logging.error(f'Domain.py: DNS lookup failed for url: {domain_name}')
        
        logging.info(f'Domain.py: Successfully returned domain features for url: {domain_name}')
        return self.feat_dict

# example = Domain()
# example.extract('https://reviewe-014035.firebaseapp.com/')
#
# for keys in example.feat_dict:
#     print(keys + " " + str(type(example.feat_dict[keys])))
#     print(example.feat_dict[keys])
#     print()
