import json
import time
from random import uniform
import requests
import numpy as np
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
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            return {'message': 'Authorization header must start with Bearer.'}

        token = parts[1]

        # jwt = verify_jwt(token)
        # if not jwt:
        #     return {'message': 'Invalid token.'}

        url = parse_URL()
        
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
        if parts[0].lower() != 'bearer' or len(parts) != 2:
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


def get_protocol(url):
    if not url.startswith(('http://', 'https://')):
        try:
            res = requests.get('http://' + url, timeout=3)
            if res.status_code == 200:
                return res.url
            else:
                return None
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


def test_url(url):
    try:
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        return False

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
        url = get_protocol(parse_URL())

        if url is None:
            return {'message': 'URL is invalid.'}

        if not test_url(url):
            return {'message': 'URL is not accessible.'}

        res = search_url(url, 'raw')
        if res['hits']['total']['value'] > 0:
            return {
                'message': 'URL already exists in Elasticsearch.',
                'url': url
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
        url = get_protocol(parse_URL())

        if url is None:
            return {'message': 'URL is invalid.'}

        if not test_url(url):
            return {'message': 'URL is not accessible.'}

        res = search_url(url, 'raw')
        if res['hits']['total']['value'] > 0:
            return {
                'message': 'URL already exists in Elasticsearch.',
                'url': url
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
        url = get_protocol(parse_URL())

        if url is None:
            return {'message': 'URL is invalid.'}

        if not test_url(url):
            return {'message': 'URL is not accessible.'}

        res = search_url(url, 'raw')
        if res['hits']['total']['value'] > 0:
            return {
                'message': 'URL already exists in Elasticsearch.',
                'url': url
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
