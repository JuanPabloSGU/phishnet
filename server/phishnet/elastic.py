from elasticsearch import Elasticsearch
from flask import current_app, g


def get_elastic():
    if 'elastic' not in g:
        g.elastic = Elasticsearch(
            current_app.config.get("ELASTICSEARCH_HOST"),
            basic_auth=(
                current_app.config.get('ELASTICSEARCH_USER'),
                current_app.config.get('ELASTICSEARCH_PASSWORD')
            ),
            timeout=60
        )
    return g.elastic


def close_elastic(e=None):
    elastic = g.pop('elastic', None)

    if elastic is not None:
        elastic.close()
