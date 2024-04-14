from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from multiprocessing import Process
import sys
import pytest
import os


sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from phishnet import create_app, start_server


@pytest.fixture(scope='module')
def app():
    app = create_app()
    yield app


@pytest.fixture(scope='module')
def client(app):
    return app.test_client()


@pytest.fixture(scope='session', autouse=True)
def server():
    server = Process(target=start_server)
    server.start()

    yield

    server.terminate()
    server.join()
