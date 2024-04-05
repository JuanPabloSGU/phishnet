import os
import pytest
import sys
from multiprocessing import Process
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from phishnet import create_app, start_server


@pytest.fixture
def app():
    app = create_app()
    
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(scope='session', autouse=True)
def server():
    server = Process(target=start_server)
    server.start()

    yield

    server.terminate()
    server.join()