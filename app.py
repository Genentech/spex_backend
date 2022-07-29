from spex_common.config import load_config
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from routes import blueprint
from flask_compress import Compress
import logging

config = load_config()
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

application = Flask(__name__)
Compress(application)

application.config.from_mapping(config)


bcrypt = Bcrypt(application)
jwt = JWTManager(application)
CORS(application, supports_credentials=True)


application.register_blueprint(blueprint)

if __name__ == '__main__':
    application.run()
