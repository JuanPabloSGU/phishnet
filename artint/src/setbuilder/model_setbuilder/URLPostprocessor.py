import numpy as np

class URLPostprocessor:

    def __init__(self, results) -> None:
        self.results = results
        
    def softmax(logits):
        exp_logits = np.exp(logits - np.max(logits))  # Subtract max for numerical stability
        return exp_logits / exp_logits.sum(axis=-1)
    
    def postprocess(self):
        preds = []
        for result in self.results:
            preds.append(self.softmax(np.array(result['outputs'][0]['data'])))
        return preds