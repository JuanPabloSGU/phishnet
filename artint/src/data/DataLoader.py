from sklearn.model_selection import train_test_split

import pandas as pd
import numpy as np

class DataLoader:
    def __init__(self, elastic_client, index='featext', scroll='2m', size=10000) -> None:
        
        self.elastic_client = elastic_client

        params = {'scroll':scroll, 'index':index, 'body':{'size': size,'query': {'match_all': {}}}}
        page = self.elastic_client.fetch_index(params) # fetch the first page of results 

        # list of dataframe pages
        df_lst = []
        df_lst.append(pd.DataFrame.from_dict([document['_source'] for document in page['hits']['hits']]))

        if page is None:
            raise ValueError("Missing Response")
        
        # capture scroll id for next page
        sid = page['_scroll_id']
        scroll_size = page['hits']['total']['value']

        # Start scrolling
        while (scroll_size > 0):
            page = self.elastic_client.scroll(scroll_id = sid, scroll = '2m') # query ELK for page
            sid = page['_scroll_id']
            scroll_size = len(page['hits']['hits'])

            df_lst.append(pd.DataFrame.from_dict([document['_source'] for document in page['hits']['hits']])) # append to dataframe list

        self.df = pd.concat(df_lst) # concatenate dataframes
        self.df.replace(r'^\s*$', np.nan, regex=True, inplace=True) # turn empty strings to NANs

        print(self.df)



    def __len__(self):
        return len(self.df)
    
    def get_feats(self):
        return list(self.df.columns)
    
    def is_float(x):
        try:
            float(x)
            return True
        except ValueError:
            return False
    
