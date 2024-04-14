from utils import generate_jwt
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from phishnet import elastic


def test_get_elastic(client):
    response = client.get("/api/v1/elastic")


    assert response.json["message"] == "Elasticsearch is running."


def test_close_elastic(app):
    with app.test_request_context():
        elastic.get_elastic()
        elastic.close_elastic()

        assert 'elastic' not in elastic.g


def test_hello_world(client):
    response = client.get("/api/v1/hello_world")

    assert response.json["message"] == "Hello, World!"
