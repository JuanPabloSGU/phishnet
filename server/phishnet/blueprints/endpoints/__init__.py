import os
import base64
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

api.add_resource(ElasticsearchResource, '/elastic')

class TestElasticsearchResource(Resource):
    def get(self):
        es = elastic.get_elastic()
        idx = 'raw'
        data = es.search(index=idx, body={'query': {'match_all': {}}}, size=100)
        return {'message': 'Test Elasticsearch!', 'data': data.body}

    def post(self):
        es = elastic.get_elastic()
        idx = 'test-data'
        es.create(index=idx, id=1, body={'test': 'data'})
        return {'message': 'Test Elasticsearch!'}

api.add_resource(TestElasticsearchResource, '/test_elastic')

class LexicalFeatureResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, required=True, help='URL to extract lexical features from.')
        args = parser.parse_args()

        url = args['url']
        if url is None:
            return {'message': 'No URL provided.'}
        
        es = elastic.get_elastic()
        res = es.search(index='featext', body={'query': {'match': {'url': url}}})

        return {'message': 'Lexical Features extracted.',
                'url': url,
                'data': res.body
                }

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, required=True, help='URL to extract lexical features from.')
        args = parser.parse_args()

        url = args['url']
        if url is None:
            return {'message': 'No URL provided.'}

        es = elastic.get_elastic()
        idx_raw = 'raw'
        idx_feat = 'featext'

        if url is None:
            return {'message': 'No URL provided.'}

        # Run Lexical Feature Extraction
        # Step 1 - Check if URL exists in Elasticsearch
        res = es.search(index=idx_raw, body={'query': {'match': {'url': url}}})
        if res['hits']['total'] == 1:
            return {'message': 'URL found in raw index, skipping feature extraction.'}

        # Step 2 - Extract Lexical Features
        lexical = Lexical([url])
        lexical.extract()
        data = lexical.feat_dict

        # Step 3 - Store Lexical Features in Elasticsearch
        es.create(index=idx_feat, id=base64.b64encode(url.encode()).decode(), body=data)

        return {'message': 'Lexical Features extracted and stored.',
                'url': url}

api.add_resource(LexicalFeatureResource, '/lexical')