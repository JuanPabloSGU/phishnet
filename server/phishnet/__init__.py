from flask import Flask
from .blueprints.endpoints import blueprint as endpoints


app = Flask(__name__)
app.config.from_pyfile('config.py')
app.register_blueprint(endpoints)

if __name__ == '__main__':
    app.run()
