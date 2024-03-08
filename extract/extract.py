import requests
import os
import sys
import pandas as pd
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def extract(url: str):
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        raise Exception(f'Error: {response.status_code}')

    return response

load_dotenv()

r = extract(os.getenv('BLOCKLIST'))

with open('blocklist.txt', 'wb') as f:
    f.write(r.content)

urls = open('extract/blocklist.txt').read().splitlines()

from artint.src.features.Lexical import Lexical

for url in urls:
    lexical = Lexical([url])
    lexical.extract()
    df = pd.DataFrame.from_dict(data=lexical.feat_dict, orient='index')
    df = df.transpose()

    with open('extract/lexical.csv', 'a') as f:
        if os.stat('extract/lexical.csv').st_size == 0:
            f.write(df.to_csv(header=True, index=False))
        f.write(df.to_csv(header=False, index=False))