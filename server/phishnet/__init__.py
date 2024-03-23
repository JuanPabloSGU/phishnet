from flask import Flask
from flask_restful import Api
from flasgger import Swagger
from .blueprints.endpoints import blueprint as endpoints


app = Flask(__name__)
app.config.from_pyfile('config.py')
app.register_blueprint(endpoints)

Api(app)
Swagger(app)

if __name__ == '__main__':
    app.run()
