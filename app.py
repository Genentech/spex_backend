from spex_common.config import load_config
from spex_common.modules.database import db_instance
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from routes import blueprint

config = load_config()

application = Flask(__name__)
application.config.from_mapping(config)


bcrypt = Bcrypt(application)
jwt = JWTManager(application)
CORS(application, supports_credentials=True)


application.register_blueprint(blueprint)

if __name__ == '__main__':
    db_instance().initialize()
    application.run()
