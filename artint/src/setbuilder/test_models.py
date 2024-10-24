from elasticsearch import Elasticsearch
import logging
from dotenv import load_dotenv
import os
import random
import requests
import json
import numpy as np
import mlflow
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import time
import subprocess

from model_setbuilder.Classical import ClassicalFeatExtractor
from model_setbuilder.URLPreprocessor import URLPreprocessor
from model_setbuilder.URLPostprocessor import URLPostprocessor

class Tester:

    def __init__(self) -> None:

        load_dotenv()

        self.host = os.getenv('ELASTICSEARCH_HOST')
        self.user = os.getenv('ELASTICSEARCH_USER')
        self.password = os.getenv('ELASTICSEARCH_PASSWORD')

        self.es_client = self.initialize_es_client()
        self.data = self.get_es_index('raw2')
        
        self.test_set_length = 500
        self.dataset = self.create_balanced_test_set()
        self.extract_urls_from_dataset()

        self.model_extractor_mapper = {
            #ClassicalFeatExtractor: ['randomForest', 'logisticalRegression', 'MLP'],
            URLPreprocessor: ['urlBert']
        }


        self.triton_server_url = "https://triton.capstone.databending.ca"
        self.mlflow_tracking_uri = "http://localhost:5000"

        

    def extract_urls_from_dataset(self):
        self.urls = [item['_source']['url'] for item in self.dataset]
        self.labels = [item['_source']['type'] for item in self.dataset]

    def create_balanced_test_set(self):
        """
        Creates a balanced test set from the given data.

        Parameters:
        data (list): List of dictionaries containing the data.

        Returns:
        list: A balanced test set with equal numbers of type 0 and type 1,
              limited to self.test_set_length total items.
        """
        # Separate data into type 0 and type 1
        type_0 = [item for item in self.data if item['_source']['type'] == 0]
        type_1 = [item for item in self.data if item['_source']['type'] == 1]

        # Calculate the number of items to select from each type
        items_per_type = min(len(type_0), len(type_1), self.test_set_length // 2)

        # Randomly sample from each type
        balanced_set = (random.sample(type_0, items_per_type) + 
                        random.sample(type_1, items_per_type))

        # Shuffle the balanced set
        random.shuffle(balanced_set)

        return balanced_set

    def initialize_es_client(self):
        """
        Initializes and returns an Elasticsearch client.

        Parameters:
        host (str): The Elasticsearch host URL.
        user (str): The username for Elasticsearch authentication.
        password (str): The password for Elasticsearch authentication.

        Returns:
        Elasticsearch: An instance of the Elasticsearch client.
        """
        logging.info('Connecting to Elasticsearch')
        es_client = Elasticsearch(
            self.host,
            basic_auth=(self.user, self.password),
            request_timeout=60
        )
        return es_client

    def get_es_index(self, index):
        """
        Retrieves all documents from the specified Elasticsearch index.

        Parameters:
        es (Elasticsearch): The Elasticsearch client instance.
        index (str): The name of the Elasticsearch index to query.

        Returns:
        list: A list of all documents retrieved from the index.
        """
        try:
            logging.info('Getting all data from Elasticsearch index: %s', index)
            query = {"query": {"match_all": {}}}
            response = self.es_client.search(index=index, body=query, scroll='1m', size=5000)
            all_data = response['hits']['hits']
            while len(response['hits']['hits']):
                response = self.es_client.scroll(scroll_id=response['_scroll_id'], scroll='1m')
                all_data += response['hits']['hits']
            logging.info('Retrieved %d documents from Elasticsearch index: %s', len(all_data), index)
            return all_data
        finally:
            self.es_client.clear_scroll(scroll_id=response['_scroll_id'])

    def triton_request(self, features, model_name):
        data = np.array(list(features.values())[1:]).astype(np.float32).tolist()

        input = 'input'
        if model_name in ['randomForest']:
            input = 'input__0'

        payload = {
            "inputs": [
                {
                    "name": input,
                    "shape": [1, len(data)],
                    "datatype": "FP32",
                    "data": data
                }
            ]
        }

        inference_url = f"{self.triton_server_url}/v2/models/{model_name}/infer"

        return requests.post(inference_url,
                            data=json.dumps(payload),
                            headers={'Content-Type': 'application/json'}
                            )

    def triton_request_bert(self, input_ids, attention_mask):
        # Set up Triton server URL
        inference_url = f"{self.triton_server_url}/v2/models/urlBert/infer"

        # Prepare the payload for inference
        payload = {
            "inputs": [
                {
                    "name": "input_ids",
                    "shape": input_ids.shape,
                    "datatype": "INT32",
                    "data": input_ids.flatten().tolist()  # Flatten the array to a list
                },
                {
                    "name": "attention_mask",
                    "shape": attention_mask.shape,
                    "datatype": "INT32",
                    "data": attention_mask.flatten().tolist()  # Flatten the array to a list
                }
            ]
        }

        # Send the request
        return requests.post(inference_url, data=json.dumps(payload), headers={"Content-Type": "application/json"})
    
    def start_mlflow_server(self):
        # Define the command to start MLflow server
        command = [
            "mlflow", "server", 
            "--backend-store-uri", "sqlite:///mlflow.db",  # SQLite for metadata
            "--default-artifact-root", "./mlruns",         # Local directory for artifacts
            "--host", "127.0.0.1",                        # Bind to localhost
            "--port", "5000"                              # Port to serve MLflow
        ]
        
        try:
            # Start MLflow server in the background and capture stdout and stderr
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Starting MLflow server...")

            # Give the server a few seconds to start up
            time.sleep(5)

            # Poll the process to check if it's still running
            if process.poll() is None:
                print("MLflow server started successfully.")
            else:
                # Server didn't start; capture and display the error
                stdout, stderr = process.communicate()
                print("Failed to start MLflow server.")
                print("Standard Output:", stdout.decode('utf-8'))
                print("Standard Error:", stderr.decode('utf-8'))
                return None
            
        except Exception as e:
            print(f"Exception occurred while starting MLflow server: {e}")
            return None
        
        return process

    def stop_mlflow_server(self, process):
        # Terminate the MLflow server process
        process.terminate()
        print("MLflow server stopped.")
        

    def establish_mlflow_connection(self):
        retries = 3
        for attempt in range(retries):
            try:
                mlflow.set_tracking_uri(self.mlflow_tracking_uri)
                mlflow.set_experiment("Phishing Detection Models")
                print("Connected to MLflow Tracking Server")
                break
            except Exception as e:
                print(f"Connection failed (attempt {attempt+1}/{retries}): {e}")
                time.sleep(5)  # Wait before retrying
        else:
            raise ConnectionError("Failed to connect to the MLflow server after several attempts")
        
    def softmax(self, logits):
        exp_logits = np.exp(logits - np.max(logits))  # Subtract max for numerical stability
        return exp_logits / exp_logits.sum(axis=-1)
    
    def test_models(self):
        proc = self.start_mlflow_server()
        self.establish_mlflow_connection()

        for extractor, models in self.model_extractor_mapper.items():
            ext = extractor(self.urls)
            feats = ext.preprocess()
            
            for model in models:
                # Start a new MLflow run for each model
                with mlflow.start_run():
                    preds = []
                    for feat in feats:
                        if extractor == ClassicalFeatExtractor:
                            res = self.triton_request(feat, model)
                            preds.append(1 if res.json()['outputs'][0]['data'][0] >= 0.5 else 0)  # binary preds
                        elif extractor == URLPreprocessor:
                            res = self.triton_request_bert(*feat)
                            preds.append(np.argmax(self.softmax(np.array(res.json()['outputs'][0]['data']))))
                            
                    # Calculate metrics
                    accuracy = accuracy_score(self.labels, preds)
                    precision = precision_score(self.labels, preds)
                    recall = recall_score(self.labels, preds)
                    f1 = f1_score(self.labels, preds)
                    
                    # Log metrics to MLflow
                    mlflow.log_metric("accuracy", accuracy)
                    mlflow.log_metric("precision", precision)
                    mlflow.log_metric("recall", recall)
                    mlflow.log_metric("f1_score", f1)
                    
                    # Log the model name as a parameter for this run
                    mlflow.log_param("model", model)
                print(f'Model {model} testing complete')

        # Optionally stop the MLflow server after all runs are complete
        #self.stop_mlflow_server(proc)

                
t = Tester()
t.test_models()