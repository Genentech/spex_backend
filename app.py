from config import config
from flask import Flask
from modules.database import database
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from routes import blueprint


application = Flask(__name__)
application.config.from_mapping(config)


bcrypt = Bcrypt(application)
jwt = JWTManager(application)
CORS(application, supports_credentials=True)


application.register_blueprint(blueprint)

if __name__ == '__main__':
    database.initialize()
    application.run(host='0.0.0.0', port='8080')
