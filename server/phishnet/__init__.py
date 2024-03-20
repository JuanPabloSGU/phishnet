import os

from flask import Flask
from . import elastic

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        ELASTICSEARCH_HOST=os.getenv('ELASTICSEARCH_HOST'),
        ELASTICSEARCH_USER=os.getenv('ELASTICSEARCH_USER'),
        ELASTICSEARCH_PASSWORD=os.getenv('ELASTICSEARCH_PASSWORD')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    elastic.init_app(app)

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app