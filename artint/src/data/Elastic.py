import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

class Elastic:
    def __init__(self, timeout: int) -> Elasticsearch:
        load_dotenv()
        self.host = os.getenv('ELASTICSEARCH_HOST')
        self.user = os.getenv('ELASTICSEARCH_USER')
        self.password = os.getenv('ELASTICSEARCH_PASSWORD')
        self.connection = Elasticsearch(
            self.host,
            basic_auth=(self.user, self.password),
            timeout=timeout
        )

    def search_entire_index(self, index: str) -> dict:
        return self.connection.search(
            http_auth=(self.user, self.password),
            index=index,
            body={
                'size': 10000,
                'query': {
                    'match_all': {}
                }
            }
        )