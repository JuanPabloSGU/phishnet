from sklearn.model_selection import train_test_split

import pandas as pd
import numpy as np

class DataLoader:
    def __init__(self, elastic_client, index='featext', scroll='2m', size=10000) -> None:
        
        self.elastic_client = elastic_client

        params = {'scroll':scroll, 'index':index, 'body':{'size': size,'query': {'match_all': {}}}}
        page = self.elastic_client.fetch_index(params)

        df_lst = []
        df_lst.append(pd.DataFrame.from_dict([document['_source'] for document in page['hits']['hits']]))

        if page is None:
            raise ValueError("Missing Response")

        sid = page['_scroll_id']
        scroll_size = page['hits']['total']['value']

        # Start scrolling
        while (scroll_size > 0):
            page = self.elastic_client.scroll(scroll_id = sid, scroll = '2m')
            sid = page['_scroll_id']
            scroll_size = len(page['hits']['hits'])

            df_lst.append(pd.DataFrame.from_dict([document['_source'] for document in page['hits']['hits']]))
        
        self.df = pd.concat(df_lst)
        self.df.replace(r'^\s*$', np.nan, regex=True, inplace=True)
        
        self.cast_astype()
        #self.lex_df = self.extract_lexical()

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
    
    def cast_astype(self):
        for col in self.df.select_dtypes(include='object').columns:
            if self.df[col].apply(lambda x: str(x).isdigit()).all():
                self.df[col] = self.df[col].astype(int)
            elif self.df[col].apply(lambda x: DataLoader.is_float(x)).all():
                self.df[col] = self.df[col].astype(float)
    
    # refactor 
    def extract_lexical(self):
        lexical_feats = ['len_url', 'len_component', 'count_digits_component', 'count_letters_component', 'ratio_digits_component_url', 'ratio_letters_component_url', 'count_dots_url', 'count_percent_url', 'count_hash_url', 'count_ats_url', 'count_embed_url', 'use_https', 'no_of_directories', 'contains_ip_address', 'character_continuity_rate_url', 'shannon_entropy_url']
        lexical_feats.append('type')
        return self.df[lexical_feats]

    def train_test_split(self, X, y, train_split, random_state): 
        return train_test_split(X, y, train_size=train_split, random_state=random_state)
