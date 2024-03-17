import os
import pandas as pd
from artint.src.features.Lexical import Lexical
from artint.src.features.Content import Content

def main(urls: list):
    for url in urls:
        # Extract lexical features
        lexical = Lexical([url])
        lexical.extract()
        df_lexical = pd.DataFrame.from_dict(data=lexical.feat_dict, orient='index')
        df_lexical = df_lexical.transpose()

        with open('extract/lexical.csv', 'a', newline='') as f:
            if os.stat('extract/lexical.csv').st_size == 0:
                f.write(df_lexical.to_csv(header=True, index=False))
            f.write(df_lexical.to_csv(header=False, index=False))

        # Extract content features
        content = Content([url])
        content.extract()
        df_content = pd.DataFrame.from_dict(data=content.feat_dict, orient='index')
        df_content = df_content.transpose()

        with open('extract/content.csv', 'a', newline='') as f: # TODO: Add column headers to content.csv
            if os.stat('extract/content.csv').st_size == 0:
                f.write(df_content.to_csv(header=True, index=False))
            f.write(df_content.to_csv(header=False, index=False))