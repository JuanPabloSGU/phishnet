
class DataLoader:
    def __init__(self, response) -> None:
        self.response = response
        self.load_feats()

        self.numeric = self.get_numeric_feats()
        self.alphabeltical = self.get_alphabetical_feats()
    
    def load_feats(self):
        hits = self.response['data']['hits']['hits']
        self.feats = list(hits[0]['_source'].keys())

        self.data = []
        for hit in hits:
            lst = []
            for feat in self.feats:
                lst.append(hit['_source'][feat])
            self.data.append(lst)
        return
    
    def get_type_feats(self, _types):
        return [self.feats[idx] for idx, hit in enumerate(self.data[0]) if isinstance(hit, _types)]
    
    def get_numeric_feats(self):
        return self.get_type_feats((int, float))

    def get_alphabetical_feats(self):
        return self.get_type_feats((str))
    
r = {}
dl = DataLoader(
    r
)

print(dl.feats)
print(dl.data)