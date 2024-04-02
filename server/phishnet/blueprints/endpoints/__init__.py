import json
import os
import requests
import base64
import numpy as np
from flask import Blueprint
from flask_restful import Api, Resource, reqparse
from flasgger import swag_from
from phishnet import elastic
from phishnet.blueprints.features.Lexical import Lexical

blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(blueprint)

class HelloWorldResource(Resource):
    @swag_from({
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

class ElasticsearchResource(Resource):
    @swag_from({
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
        es = elastic.get_elastic().info(pretty=True)
        return {'message': 'Hello, ElasticSearch!', 'info': es.body}


class LogisticalRegression(Resource):
    @swag_from({
        'parameters': [
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
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, required=True, help='URL to extract lexical features from.')
        args = parser.parse_args()

        url = args['url']
        if url is None:
            return {'message': 'No URL provided.'}

        es = elastic.get_elastic()
        idx_raw = 'raw'
        idx_feat = 'test_feat'

        # Run Lexical Feature Extraction
        # Step 1 - Check if URL exists in Elasticsearch
        res = es.search(
            index=idx_raw,
            body={
                'query': {
                    'term': {
                        'url.keyword': url
                    }
                }
            }
        )
        if res['hits']['total']['value'] > 0:
            return {'message': 'URL found in raw index, skipping feature extraction.'}

        # Step 2 - Extract Lexical Features
        lexical = Lexical()
        lexical.extract(url)
        features = lexical.feat_dict

        # Step 3 - Store Lexical Features in Elasticsearch
        es.index(index=idx_feat, body=features)

        data = np.array(list(features.values())[1:]).astype(np.float32).tolist()

        payload = {
            "inputs": [
                {
                    "name": "input",
                    "shape": [1, len(data)],
                    "datatype": "FP32",
                    "data": data
                }
            ]
        }

        triton_server_url = "https://triton.capstone.databending.ca"
        model_name = "logisticalRegression"
        inference_url = f"{triton_server_url}/v2/models/{model_name}/infer"

        res = requests.post(inference_url, 
                            data=json.dumps(payload),
                            headers={'Content-Type': 'application/json'}
                            )

        return {'message': 'Lexical Features extracted and stored.',
                'url': url,
                'data': features,
                'triton': res.json()}

api.add_resource(LogisticalRegression, '/logres')