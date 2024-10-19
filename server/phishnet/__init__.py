from flask import Flask
from flask_restful import Api
from flasgger import Swagger
from .blueprints.endpoints import blueprint as endpoints


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    app.register_blueprint(endpoints)

    Api(app)
    Swagger(app)
    return app


def start_server():
    app = create_app()
    app.run()


if __name__ == '__main__':
    start_server()
