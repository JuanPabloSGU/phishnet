import json
import time
from random import uniform
import requests
import numpy as np
from transformers import BertTokenizer
import tensorflow as tf
from flask import Blueprint, request, current_app
from flask_restful import Api, Resource, reqparse
from flasgger import swag_from
from phishnet import elastic
from phishnet.blueprints.features.Lexical import Lexical
from flask_cors import CORS
from authlib.jose import jwt
from jwcrypto import jwk


blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(blueprint)
CORS(blueprint)

def get_public_key(n, e):
    public_key = jwk.JWK(
            kty='RSA',
            n=n,
            e=e,
            alg='RS256'
            )

    return public_key.export_to_pem(private_key=False, password=False).decode('utf-8')

def verify_jwt(token):
    public_keys = current_app.config['JWT_PUBLIC_KEYS']

    for key in public_keys:
        public_key_pem = get_public_key(key['n'], key['e'])

        try:
            claims = jwt.decode(token, public_key_pem, claims_options={'iss': {'essential': True, 'value': 'https://zitadel.databending.ca'}})
            return claims
        except Exception as e:
            continue

    return None


class HelloWorldResource(Resource):
    @ swag_from({
        'responses': {
            200: {
                'description': 'Hello, World!',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {
                            'type': 'string'
                        }
                    }
                }
            }
        }
    })
    def get(self):
        return {'message': 'Hello, World!'}


api.add_resource(HelloWorldResource, '/hello_world')

class LLMMockResource(Resource):
    @ swag_from({
        'parameters': [
            {
                'name': 'Authorization',
                'description': 'JWT',
                'in': 'header',
                'type': 'string',
                'required': True
            },
            {
                'name': 'url',
                'description': 'URL to extract lexical features from.',
                'in': 'formData',
                'type': 'string',
                'required': True
            }
        ],
        'responses': {
            200: {
                'description': 'Lexical Features extracted and stored.',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {
                            'type': 'string'
                        },
                        'url': {
                            'type': 'string'
                        },
                        'data': {
                            'type': 'object'
                        }
                    }
                }
            }
        }
    })
    def post(self): 
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return {'message': 'Authorization header is required.'}

        parts = auth_header.split()
        if parts[0].lower() == 'bearer' and len(parts) != 2:
            return {'message': 'Token must be present with Bearer.'}
        elif parts[0].lower() != 'bearer' or len(parts) != 2:
            return {'message': 'Authorization header must start with Bearer.'}

        token = parts[1]

        # jwt = verify_jwt(token)
        # if not jwt:
        #     return {'message': 'Invalid token.'}

        url = get_protocol(parse_URL())

        if url is None:
            return {'message': 'URL is invalid.'}

        percentage = float("{:.2f}".format(uniform(0, 1)*100))

        # wait between 500ms and 2s 
        time.sleep(uniform(0.1, 1))
        return {'message': f'{percentage}%'}


api.add_resource(LLMMockResource, '/llm_mock')

class UserResource(Resource):
    @ swag_from({
        'parameters': [
            {
                'name': 'Authorization',
                'description': 'JWT Token',
                'in': 'header',
                'type': 'string',
                'required': True
            }
        ],
        'responses': {
            200: {
                'description': 'Hello, User!',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {
                            'type': 'string'
                        }
                    }
                }
            }
        }
    })
    def get(self):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return {'message': 'Authorization header is required.'}

        parts = auth_header.split()
        if parts[0].lower() == 'bearer' and len(parts) != 2:
            return {'message': 'Token must be present with Bearer.'}
        elif parts[0].lower() != 'bearer' or len(parts) != 2:
            return {'message': 'Authorization header must start with Bearer.'}

        token = parts[1]

        jwt = verify_jwt(token)
        if not jwt:
            return {'message': 'Invalid token.'}

        return {'msg': f'Hello, {jwt["name"]}!'}


api.add_resource(UserResource, '/user')


class ElasticsearchResource(Resource):
    @ swag_from({
        'parameters': [
            {
                'name': 'Authorization',
                'description': 'JWT Token',
                'in': 'header',
                'type': 'string',
                'required': True
            }
        ],
        'responses': {
            200: {
                'description': 'Hello, ElasticSearch!',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {
                            'type': 'string'
                        },
                        'info': {
                            'type': 'object'
                        }
                    }
                }
            }
        }
    })
    def get(self):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return {'message': 'Authorization header is required.'}

        parts = auth_header.split()
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            return {'message': 'Authorization header must start with Bearer.'}

        token = parts[1]

        jwt = verify_jwt(token)
        if not jwt:
            return {'message': 'Invalid token.'}

        es = elastic.get_elastic().info(pretty=True)
        return {'message': 'Elasticsearch is running.', 'info': es.body}


api.add_resource(ElasticsearchResource, '/elastic')


def parse_URL():
    parser = reqparse.RequestParser()
    parser.add_argument('url',
                        type=str,
                        required=True,
                        help='URL for method is required.')

    args = parser.parse_args()
    return args['url']


def search_url(url, index):
    es = elastic.get_elastic()
    res = es.search(
        index=index,
        body={
            'query': {
                'term': {
                    'url.keyword': url
                }
            }
        }
    )
    return res


def store_features(features, index):
    es = elastic.get_elastic()
    es.index(index=index, body=features)


def triton_request(features, model_name, input):
    data = np.array(list(features.values())[1:]).astype(np.float32).tolist()

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

    triton_server_url = "https://triton.capstone.databending.ca"
    inference_url = f"{triton_server_url}/v2/models/{model_name}/infer"

    res = requests.post(inference_url,
                        data=json.dumps(payload),
                        headers={'Content-Type': 'application/json'}
                        )

    return res

def triton_requestBert(input_ids, attention_mask):
    # Set up Triton server URL
    triton_server_url = "https://triton.capstone.databending.ca"
    inference_url = f"{triton_server_url}/v2/models/urlBert/infer"

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

def triton_request_htmlgcncnn(graph, cnn_input):
    """
    Sends a request to the Triton server with the provided graph and CNN input.

    Args:
        graph (dict): A dictionary containing 'x', 'edge_index', and 'batch' tensors of the graph.
        cnn_input (tensor): A tensor representing the CNN input.

    Returns:
        Response: The response from the Triton server.
    """
    triton_server_url = "https://triton.capstone.databending.ca"
    inference_url = f"{triton_server_url}/v2/models/htmlGraphCnn/infer"

    # Convert graph components and CNN input to lists for JSON payload
    graph_data_x = graph['x'].numpy().tolist()
    graph_edge_index = graph['edge_index'].numpy().tolist()
    graph_batch = graph['batch'].numpy().tolist()
    cnn_input_data = cnn_input.numpy().tolist()

    # Build the payload for Triton server
    payload = {
        "inputs": [
            {
                "name": "graph_data.x",
                "shape": list(graph['x'].shape),
                "datatype": "FP32",
                "data": graph_data_x
            },
            {
                "name": "graph_data.edge_index",
                "shape": list(graph['edge_index'].shape),
                "datatype": "INT64",
                "data": graph_edge_index
            },
            {
                "name": "graph_data.batch",
                "shape": list(graph['batch'].shape),
                "datatype": "INT64",
                "data": graph_batch
            },
            {
                "name": "x_seq",
                "shape": list(cnn_input.shape),
                "datatype": "INT64",
                "data": cnn_input_data
            }
        ]
    }

    # Send the POST request to the Triton server
    response = requests.post(
        inference_url, 
        data=json.dumps(payload), 
        headers={"Content-Type": "application/json"}
    )

    return response

def get_protocol(url):
    if not url.startswith(('http://', 'https://')):
        try:
            res = requests.get('http://' + url, timeout=3)
            res.status_code == 200
            return res.url
        except requests.exceptions.RequestException:
            return None

        try:
            res = requests.get('https://' + url, timeout=3)
            if res.status_code == 200:
                return res.url
            else:
                return None
        except requests.exceptions.RequestException:
            return None

    return url

def urlFormatting(url):
    url = url.replace("www.", "")
    url = url.replace("https://", "")
    url = url.replace("http://", "")
    return url.rstrip("/")

def retrieveTokenizer(url):
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

def test_url(url):
    try:
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        return False

class LogisticalRegression(Resource):
    @ swag_from({
        'parameters': [
            {
                'name': 'url',
                'description': 'URL to extract lexical features from.',
                'in': 'formData',
                'type': 'string',
                'required': True
            },
            {
                'name': 'Authorization',
                'description': 'JWT Token',
                'in': 'header',
                'type': 'string',
                'required': True
            }
        ],
        'responses': {
            200: {
                'description': 'Lexical Features extracted and stored.',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {
                            'type': 'string'
                        },
                        'url': {
                            'type': 'string'
                        },
                        'data': {
                            'type': 'object'
                        }
                    }
                }
            }
        },
    })
    def post(self):
        # Authentication
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return {'message': 'Authorization header is required.'}

        parts = auth_header.split()
        if parts[0].lower() == 'bearer' and len(parts) != 2:
            return {'message': 'Token must be present with Bearer.'}
        elif parts[0].lower() != 'bearer' or len(parts) != 2:
            return {'message': 'Authorization header must start with Bearer.'}

        token = parts[1]

        jwt = verify_jwt(token)
        if not jwt:
            return {'message': 'Invalid token.'}
        #End of authentication

        url = get_protocol(parse_URL())

        if url is None:
            return {'message': 'URL is invalid.'}

        if not test_url(url):
            return {'message': 'URL is not accessible.'}

        res = search_url(url, 'raw2')
        if res['hits']['total']['value'] > 0:
            first_hit = res['hits']['hits'][0]
            type_value = first_hit['_source']['type']
            triton_response = {
                "model_name": "logisticalRegression",
                "model_version": "1",
                "outputs": [
                    {
                        "name": "logits",
                        "datatype": "FP32",
                        "shape": [1, 2],
                        "data": str([float(type_value)])
                    }
                ]
            }

            return {
                'message': 'Lexical Features extracted and stored.',
                'url': url,
                'triton': triton_response
            }

        lexical = Lexical()
        lexical.extract(url)
        features = lexical.feat_dict

        # Step 3 - Store Lexical Features in Elasticsearch
        store_features(features, 'test_feat')

        # Step 4 - Send Lexical Features to Triton
        res = triton_request(features, 'logisticalRegression', 'input')



        return {'message': 'Lexical Features extracted and stored.',
                'url': url,
                'data': features,
                'triton': res.json()}


api.add_resource(LogisticalRegression, '/logres')


class RandomForest(Resource):
    @ swag_from({
        'parameters': [
            {
                'name': 'url',
                'description': 'URL to extract lexical features from.',
                'in': 'formData',
                'type': 'string',
                'required': True
            },
            {
                'name': 'Authorization',
                'description': 'JWT Token',
                'in': 'header',
                'type': 'string',
                'required': True
            }
        ],
        'responses': {
            200: {
                'description': 'Lexical Features extracted and stored.',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {
                            'type': 'string'
                        },
                        'url': {
                            'type': 'string'
                        },
                        'data': {
                            'type': 'object'
                        }
                    }
                }
            }
        }
    })
    def post(self):
        # Authentication
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return {'message': 'Authorization header is required.'}

        parts = auth_header.split()
        if parts[0].lower() == 'bearer' and len(parts) != 2:
            return {'message': 'Token must be present with Bearer.'}
        elif parts[0].lower() != 'bearer' or len(parts) != 2:
            return {'message': 'Authorization header must start with Bearer.'}

        token = parts[1]

        jwt = verify_jwt(token)
        if not jwt:
            return {'message': 'Invalid token.'}
        #End of authentication

        url = get_protocol(parse_URL())

        if url is None:
            return {'message': 'URL is invalid.'}

        if not test_url(url):
            return {'message': 'URL is not accessible.'}

        res = search_url(url, 'raw2')
        if res['hits']['total']['value'] > 0:
            first_hit = res['hits']['hits'][0]
            type_value = first_hit['_source']['type']

            # Construct the triton response
            triton_response = {
                "model_name": "randomForest",
                "model_version": "1",
                "outputs": [
                    {
                        "name": "predictions",
                        "datatype": "FP32",
                        "shape": [1, 2],
                        "data": str([float(type_value)])
                    }
                ]
            }

            return {
                'message': 'Lexical Features extracted and stored.',
                'url': url,
                'triton': triton_response
            }

        lexical = Lexical()
        lexical.extract(url)
        features = lexical.feat_dict

        # Step 3 - Store Lexical Features in Elasticsearch
        store_features(features, 'test_feat')

        # Step 4 - Send Lexical Features to Triton
        res = triton_request(features, 'randomForest', 'input__0')

        return {'message': 'Lexical Features extracted and stored.',
                'url': url,
                'data': features,
                'triton': res.json()}


api.add_resource(RandomForest, '/randforest')


class MLPResource(Resource):
    @ swag_from({
        'parameters': [
            {
                'name': 'url',
                'description': 'URL to extract lexical features from.',
                'in': 'formData',
                'type': 'string',
                'required': True
            },
            {
                'name': 'Authorization',
                'description': 'JWT Token',
                'in': 'header',
                'type': 'string',
                'required': True
            }
        ],
        'responses': {
            200: {
                'description': 'Lexical Features extracted and stored.',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {
                            'type': 'string'
                        },
                        'url': {
                            'type': 'string'
                        },
                        'data': {
                            'type': 'object'
                        }
                    }
                }
            }
        }
    })
    def post(self):
        # Authentication
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return {'message': 'Authorization header is required.'}

        parts = auth_header.split()
        if parts[0].lower() == 'bearer' and len(parts) != 2:
            return {'message': 'Token must be present with Bearer.'}
        elif parts[0].lower() != 'bearer' or len(parts) != 2:
            return {'message': 'Authorization header must start with Bearer.'}

        token = parts[1]

        jwt = verify_jwt(token)
        if not jwt:
            return {'message': 'Invalid token.'}
        #End of authentication

        url = get_protocol(parse_URL())

        if url is None:
            return {'message': 'URL is invalid.'}

        if not test_url(url):
            return {'message': 'URL is not accessible.'}

        res = search_url(url, 'raw2')
        if res['hits']['total']['value'] > 0:
            first_hit = res['hits']['hits'][0]
            type_value = first_hit['_source']['type']

            # Construct the triton response
            triton_response = {
                "model_name": "MLP",
                "model_version": "1",
                "outputs": [
                    {
                        "name": "predictions",
                        "datatype": "FP32",
                        "shape": [1, 2],
                        "data": str([float(type_value)])
                    }
                ]
            }

            return {
                'message': 'Lexical Features extracted and stored.',
                'url': url,
                'triton': triton_response
            }

        lexical = Lexical()
        lexical.extract(url)
        features = lexical.feat_dict

        # Step 3 - Store Lexical Features in Elasticsearch
        store_features(features, 'test_feat')

        # Step 4 - Send Lexical Features to Triton
        res = triton_request(features, 'MLP', 'input')

        return {'message': 'Lexical Features extracted and stored.',
                'url': url,
                'data': features,
                'triton': res.json()}


api.add_resource(MLPResource, '/mlp')

class UrlBertResource(Resource):
    @ swag_from({
        'parameters': [
            {
                'name': 'url',
                'description': 'URL to make inference.',
                'in': 'formData',
                'type': 'string',
                'required': True
            },
            {
                'name': 'Authorization',
                'description': 'JWT Token',
                'in': 'header',
                'type': 'string',
                'required': True
            }
        ],
        'responses': {
            200: {
                'description': 'Inference to urlBert.',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {
                            'type': 'string'
                        },
                        'url': {
                            'type': 'string'
                        },
                        'data': {
                            'type': 'object'
                        }
                    }
                }
            }
        }
    })
    def post(self):
        # Authentication
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return {'message': 'Authorization header is required.'}

        parts = auth_header.split()
        if parts[0].lower() == 'bearer' and len(parts) != 2:
            return {'message': 'Token must be present with Bearer.'}
        elif parts[0].lower() != 'bearer' or len(parts) != 2:
            return {'message': 'Authorization header must start with Bearer.'}

        token = parts[1]

        jwt = verify_jwt(token)
        if not jwt:
            return {'message': 'Invalid token.'}
        #End of authentication

        url = get_protocol(parse_URL())

        if url is None:
            return {'message': 'URL is invalid.'}

        if not test_url(url):
            return {'message': 'URL is not accessible.'}

        res = search_url(url, 'raw2')
        if res['hits']['total']['value'] > 0:
            first_hit = res['hits']['hits'][0]
            type_value = first_hit['_source']['type']

            # Construct the triton response
            triton_response = {
                "model_name": "urlBert",
                "model_version": "2",
                "outputs": [
                    {
                        "name": "logits",
                        "datatype": "FP32",
                        "shape": [1, 2],
                        "data": str([float(type_value)])
                    }
                ]
            }

            return {
                'message': 'Url Inference complete.',
                'url': url,
                'triton': triton_response
            }

        # Set the url in the proper format
        transformedInput = urlFormatting(url)

        # Create the input and attention mask for inference
        input_ids, attention_mask = retrieveTokenizer(transformedInput)
        
        # Step 3 - Send tokens to Triton
        res = triton_requestBert(input_ids, attention_mask)
    
        # Replace the logit answer into a probablity between 0 and 1
        result = res.json()
        logits = np.array(result['outputs'][0]['data'])
        prediction = tf.nn.softmax(logits, axis=-1)[1]

        prediction = [prediction.numpy().item()] 

        result['outputs'][0]['data'] = str(prediction)

        return {'message': 'Url Inference complete.',
                'url': url,
                'data': input_ids.tolist(),
                'triton': result}

api.add_resource(UrlBertResource, '/urlBert')

#########################################################################################################

import aiohttp
import asyncio
import bs4
import networkx as nx
from collections import deque
from torch_geometric.utils import from_networkx
import torch
import time

def get_html_content(url, timeout=15, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    print(f"Failed to fetch {url} after {retries} attempts.")
    return None

def parse_html(html_content):
    """
    Parses the HTML document and returns a DOM tree using BeautifulSoup.
    """
    soup = bs4.BeautifulSoup(html_content, 'html.parser')
    return soup

def build_graph(dom_tree):
    """
    Builds a graph representation of the HTML DOM tree.
    Attributes text only to the most specific node that contains it.
    """
    if dom_tree is None:
        return 0
    
    graph = nx.DiGraph()
    queue = deque([dom_tree])
    
    while queue:
        node = queue.popleft()
        
        if node.name:  # Only consider actual HTML tags
            # Get direct text content (excluding nested tags' text)
            # This gets only the text directly inside this tag, not from children
            direct_text = ''.join(child for child in node.children 
                                if isinstance(child, str)).strip()
            
            # Add node with tag and only its direct text content
            graph.add_node(id(node), 
                         tag=node.name,
                         text=direct_text)
            
            # Add all the children of the current node
            for child in node.children:
                if child.name:  # Only consider valid HTML tags
                    child_direct_text = ''.join(c for c in child.children 
                                              if isinstance(c, str)).strip()
                    graph.add_node(id(child), 
                                 tag=child.name,
                                 text=child_direct_text)
                    graph.add_edge(id(node), id(child))
                    queue.append(child)
    
    return graph

def process_html_file(html_content):
        
    text = str(html_content)
    # Parse the HTML document into a DOM tree
    dom_tree = parse_html(text)
    # Build the graph from the DOM tree
    graph = build_graph(dom_tree)
    return [graph], [text]


HTML_TAGS = [
    # Basic structure
    'html', 'head', 'body', 'title', 'meta',
    
    # Headers
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    
    # Text content
    'p', 'span', 'div', 'br', 'hr',
    
    # Links and media
    'a', 'img', 'iframe', 'video', 'audio',
    
    # Lists
    'ul', 'ol', 'li', 'dl', 'dt', 'dd',
    
    # Tables
    'table', 'tr', 'td', 'th', 'thead', 'tbody',
    
    # Forms - important for phishing
    'form', 'input', 'button', 'select', 'option', 'textarea', 'label',
    
    # Scripts and styling
    'script', 'style', 'link', 'noscript',
    
    # Semantic elements
    'nav', 'header', 'footer', 'main', 'section', 'article'
]

# Function to one-hot encode the HTML tags
def one_hot_encode_tag(tag, tag_set):
    encoding = np.zeros(len(tag_set))
    if tag in tag_set:
        encoding[tag_set.index(tag)] = 1
    return encoding

# Convert the networkx graph to PyG data format and prepare node features
def convert_to_pyg_graph(graph):
    # Prepare node features (one-hot encoded tags and text presence)
    node_features = []
    for node, data in graph.nodes(data=True):
        tag = data['tag']  # Get the tag
        text = data['text']  # Get the text content
        
        # One-hot encode the tag
        tag_encoding = one_hot_encode_tag(tag, HTML_TAGS)
        
        # Add binary feature for text presence
        has_text = 1.0 if text.strip() else 0.0
        
        # Combine features
        features = np.append(tag_encoding, has_text)
        node_features.append(features)

    # Convert node features to a tensor
    node_features = torch.tensor(node_features, dtype=torch.float32)

    # Convert networkx graph to a PyTorch Geometric graph
    pyg_graph = from_networkx(graph)
    pyg_graph.x = node_features

    return pyg_graph

# Function to process and convert all graphs in the list
def convert_all_graphs_to_pyg(graphs):
    pyg_graphs = []
    for i, graph in enumerate(graphs):
        pyg_graph = convert_to_pyg_graph(graph)  # Convert each networkx graph to PyG format
        pyg_graphs.append(pyg_graph)  # Store the converted PyG graph
    
    return pyg_graphs

def normalize_token(token):
    """
    Normalize tokens by lowercasing and stripping excessive whitespace.
    """
    return token.lower().strip()

def encode_html(html_string, token_to_idx, max_tokens=100):
    """
    Convert HTML string to token index sequence with normalization.
    """
    tokens = []
    soup = bs4.BeautifulSoup(html_string, 'html.parser')

    for element in soup.descendants:
        if element.name:
            tokens.append(normalize_token(f"<{element.name}>"))
            for attr in ['href', 'src', 'class', 'id']:
                if attr in element.attrs:
                    value = str(element.attrs[attr])[:30]  # Cap length of attribute values
                    tokens.append(normalize_token(f"{attr}={value}"))
        elif isinstance(element, bs4.NavigableString):
            text = normalize_token(str(element))
            if text:
                tokens.extend(text.split())

    # Convert tokens to indices
    indices = [token_to_idx.get(token, token_to_idx['<unk>']) for token in tokens[:max_tokens]]

    # Pad to max_tokens
    if len(indices) < max_tokens:
        indices += [token_to_idx['<pad>']] * (max_tokens - len(indices))

    return torch.tensor(indices, dtype=torch.long)


class HTMLGCNCNN(Resource):
    @ swag_from({
        'parameters': [
            {
                'name': 'url',
                'description': 'URL to make inference.',
                'in': 'formData',
                'type': 'string',
                'required': True
            },
            {
                'name': 'Authorization',
                'description': 'JWT Token',
                'in': 'header',
                'type': 'string',
                'required': True
            }
        ],
        'responses': {
            200: {
                'description': 'Inference to urlBert.',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {
                            'type': 'string'
                        },
                        'url': {
                            'type': 'string'
                        },
                        'data': {
                            'type': 'object'
                        }
                    }
                }
            }
        }
    })
    def post(self):
        # Authentication
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return {'message': 'Authorization header is required.'}

        parts = auth_header.split()
        if parts[0].lower() == 'bearer' and len(parts) != 2:
            return {'message': 'Token must be present with Bearer.'}
        elif parts[0].lower() != 'bearer' or len(parts) != 2:
            return {'message': 'Authorization header must start with Bearer.'}

        token = parts[1]

        jwt = verify_jwt(token)
        if not jwt:
            return {'message': 'Invalid token.'}
        #End of authentication

        url = get_protocol(parse_URL())

        if url is None:
            return {'message': 'URL is invalid.'}

        if not test_url(url):
            return {'message': 'URL is not accessible.'}

        res = search_url(url, 'raw2')
        if res['hits']['total']['value'] > 0:
            first_hit = res['hits']['hits'][0]
            type_value = first_hit['_source']['type']

            # Construct the triton response
            triton_response = {
                "model_name": "htmlGraphCnn",
                "model_version": "1",
                "outputs": [
                    {
                        "name": "predictions",
                        "datatype": "FP32",
                        "shape": [1, 2],
                        "data": str([float(type_value)])
                    }
                ]
            }

            return {
                'message': 'Url Inference complete.',
                'url': url,
                'triton': triton_response
            }
        
        html_content = get_html_content(url)

        if html_content is None:
            
            # Set the url in the proper format
            transformedInput = urlFormatting(url)

            # Create the input and attention mask for inference
            input_ids, attention_mask = retrieveTokenizer(transformedInput)
            
            # Step 3 - Send tokens to Triton
            res = triton_requestBert(input_ids, attention_mask)
        
        else:
            graphs, texts = process_html_file(html_content)
            pyg_graph = convert_all_graphs_to_pyg(graphs)

            import os
            
            print(os.path.dirname(__file__))
            vocab_path = os.path.join(os.path.dirname(__file__), '..', 'utils', 'token_to_idx.json')
            #vocab_path = 'phishnet/blueprints/utils/token_to_idx.json'
            with open(vocab_path, 'r') as f:
                token_to_idx = json.load(f)

            encoded = encode_html(texts[0], token_to_idx)
            print(encoded.shape)

            graph = {
                'x': pyg_graph[0]['x'],
                'edge_index': pyg_graph[0]['edge_index'],
                'batch': torch.zeros(pyg_graph[0]['num_nodes'], dtype=torch.long)
            }
            
            # Step 3 - Send tokens to Triton
            res = triton_request_htmlgcncnn(graph, encoded.unsqueeze(0))
        
        result = res.json()
        
        logits = np.array(result['outputs'][0]['data'])
        prediction = tf.nn.softmax(logits, axis=-1)[1]

        prediction = [prediction.numpy().item()] 

        result['outputs'][0]['data'] = str(prediction)

        return {'message': 'Url Inference complete.',
                'url': url,
                'triton': result}

api.add_resource(HTMLGCNCNN, '/htmlGraphCnn')