import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

class Elastic:
    def __init__(self, timeout: int) -> Elasticsearch:
        
        load_dotenv()
        # get environment variables
        self.host = os.getenv('ELASTICSEARCH_HOST')
        self.user = os.getenv('ELASTICSEARCH_USER')
        self.password = os.getenv('ELASTICSEARCH_PASSWORD')

        # establish connection to ELK
        self.connection = Elasticsearch(
            self.host,
            basic_auth=(self.user, self.password),
            timeout=timeout
        )

    # Query ELK, limited response (10000)
    def fetch_index(self, params) -> dict:
        return self.connection.search(
            http_auth=(self.user, self.password),
            **params
        )

    # Query ELK, limited response (10000); returns scroll index for next page
    def scroll(self, scroll_id, scroll = '2m'):
        return self.connection.scroll(
            http_auth=(self.user, self.password),
            scroll_id = scroll_id, 
            scroll = scroll
        )