from Elastic import Elastic
from sklearn.model_selection import train_test_split

import pandas as pd

class DataLoader:
    def __init__(self, response) -> None:
        self.response = response
        self.load_feats()

        self.numeric = self.get_numeric_feats()
        self.alphabeltical = self.get_alphabetical_feats()
    
    def load_feats(self):
        hits = self.response['hits']['hits']
        self.feats = list(hits[0]['_source'].keys())

        self.data = []
        for hit in hits:
            lst = []
            for feat in self.feats:
                lst.append(hit['_source'][feat])
            self.data.append(lst)
        return
    
    def to_df(self):
        self.df = pd.DataFrame(self.data, columns=self.feats)
    
    def head_tail(self):
        return self.df.head(5), self.df.tail(5)
    
    def info(self):
        return self.df.info()
    
    def count_duplicates(self):
        return self.df.groupby(self.df.columns.tolist(),as_index=False).size()
    
    def num_null_values(self):
        return self.df.isnull().sum()

    def num_uniques(self):
        return self.df.nunique()
    
    def statistical_analysis(self):
        return self.df.describe().T

    def get_type_feats(self, _types):
        return [self.feats[idx] for idx, hit in enumerate(self.data[0]) if isinstance(hit, _types)]
    
    def get_numeric_feats(self):
        return self.get_type_feats((int, float))

    def get_alphabetical_feats(self):
        return self.get_type_feats((str))
    
    def train_test_split(self, train_split, random_state): 
        return train_test_split(self.data, train_size=train_split, random_state=random_state)
    
elastic_connection = Elastic(timeout=5)

dl = DataLoader(
    elastic_connection.search_entire_index('featext')
)

dl.to_df()