import click
from elasticsearch import Elasticsearch
from flask import current_app, g

def connect_elasticsearch():
    if 'db' not in g:
        g.db = Elasticsearch(
            current_app.config['ELASTICSEARCH_HOST'],
            basic_auth=(current_app.config['ELASTICSEARCH_USER'], current_app.config['ELASTICSEARCH_PASSWORD']),
            request_timeout=60
        )

    return g.db

def close_elasticsearch(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()
    
def init_elasticsearch_command():
    connect_elasticsearch()
    click.echo('Connected to Elasticsearch')
    
def init_app(app):
    app.teardown_appcontext(close_elasticsearch)
    app.cli.add_command(init_elasticsearch_command)