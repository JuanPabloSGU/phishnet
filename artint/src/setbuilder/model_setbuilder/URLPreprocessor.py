from transformers import BertTokenizer
import numpy as np

class URLPreprocessor:

    def __init__(self, urls) -> None:
        self.urls = urls

    def preprocess(self):
        dset = []
        for url in self.urls:
            formatted_url = self.url_formatter(url)
            dset.append(self.retrieveTokenizer(formatted_url))
        return dset

    def url_formatter(self, url):
        url = url.replace("www.", "")
        url = url.replace("https://", "")
        url = url.replace("http://", "")
        return url.rstrip("/")

    def retrieveTokenizer(self, url):
    # Initialize the BERT tokenizer
        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

        # Tokenize and encode the URLs
        infer_encodings = tokenizer(url, truncation=True, padding='max_length', max_length=64)

        # Extract input_ids and attention_mask
        input_ids = infer_encodings['input_ids']
        attention_mask = infer_encodings['attention_mask']

        # Convert to numpy arrays for Triton, ensuring proper shape
        input_ids = np.array(input_ids, dtype=np.int32).reshape(1, 64)  # Shape should be (1, 64)
        #attention_mask = np.array(attention_mask, dtype=np.int32).reshape(1, 64)
        attention_mask = np.array([1]*64).reshape(1, 64)

        return input_ids, attention_mask