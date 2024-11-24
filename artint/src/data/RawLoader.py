import logging 

class RawLoader:

    def __init__(self):
        pass

    def get_es_index(self, es, index):
        """
        Retrieves all documents from the specified Elasticsearch index.

        Parameters:
        es (Elasticsearch): The Elasticsearch client instance.
        index (str): The name of the Elasticsearch index to query.

        Returns:
        list: A list of all documents retrieved from the index.
        """
        try:
            logging.info('Getting all data from Elasticsearch index: %s', index)
            query = {"query": {"match_all": {}}}
            response = es.search(index=index, body=query, scroll='1m', size=5000)
            all_data = response['hits']['hits']
            while len(response['hits']['hits']):
                response = es.scroll(scroll_id=response['_scroll_id'], scroll='1m')
                all_data += response['hits']['hits']
            logging.info('Retrieved %d documents from Elasticsearch index: %s', len(all_data), index)
            return all_data
        finally:
            es.clear_scroll(scroll_id=response['_scroll_id'])