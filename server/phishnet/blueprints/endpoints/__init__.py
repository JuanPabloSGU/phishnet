from flask import Blueprint
from flask_restful import Api, Resource
from flasgger import swag_from
from phishnet import elastic

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
        es = elastic.get_elastic().info()
        return {'message': 'Hello, ElasticSearch!', 'info': es}

api.add_resource(ElasticsearchResource, '/elastic')