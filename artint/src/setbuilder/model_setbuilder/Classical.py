import sys
import os

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

# Now you can import using the absolute import
from src.features.Lexical import Lexical

class ClassicalFeatExtractor:

    def __init__(self, urls) -> None:
        self.urls = urls
        self.feat_extractor = Lexical()

    def preprocess(self):
        feat_arr = []
        for url in self.urls:
            self.feat_extractor.extract(url)
            feat_arr.append(self.feat_extractor.feat_dict)
        return feat_arr