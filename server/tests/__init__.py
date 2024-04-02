import os
import pytest
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from phishnet import create_app


@pytest.fixture
def app():
    app = create_app()
    
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


def test_request_example(client):
    response = client.get("/api/v1/hello_world")
    assert response.json["message"] == "Hello, World!"

def test_elastic_search(client):
    response = client.get("/api/v1/elastic")
    assert response.json["message"] == "Hello, ElasticSearch!"