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
