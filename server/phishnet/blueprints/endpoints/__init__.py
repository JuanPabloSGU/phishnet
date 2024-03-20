from flask import Blueprint
from phishnet import elastic

blueprint = Blueprint('api', __name__, url_prefix='/api/v1')

@blueprint.route('/hello_world')
def hello_world():
    return {'message': 'Hello, World!'}


@blueprint.route('/elastic')
def elasticsearch():
    es = elastic.get_elastic().info()
    return {'message': 'Hello, ElasticSearch!',
            'info': es
            }
