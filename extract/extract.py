import os
import pandas as pd
from artint.src.features.Content import Content
from artint.src.features.Domain import Domain
from artint.src.features.Lexical import Lexical

def extract_features(feature_class, output_file, url):
    feature_extractor = feature_class([url])
    feature_extractor.extract()
    df = pd.DataFrame.from_dict(data=feature_extractor.feat_dict, orient='index')
    df = df.transpose()

    with open(output_file, 'a', newline='') as f:
        if os.stat(output_file).st_size == 0:
            f.write(df.to_csv(header=True, index=False))
        f.write(df.to_csv(header=False, index=False))

def main(urls: list):
    for url in urls:
        # Extract lexical features
        extract_features(Lexical, 'extract/lexical.csv', url)

        # Extract content features
        # TODO: Figure out why column headers are missing in content.csv
        extract_features(Content, 'extract/content.csv', url) 

        # Extract domain features
        extract_features(Domain, 'extract/domain.csv', url)