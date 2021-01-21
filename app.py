from flask import Flask
from database.config import config
from database.db import ArangoDB
from flask_restx import Api
from flask_bcrypt import Bcrypt
# from flask_cors import CORS
from routes.auth_router import register as userApi
from routes.auth_router import users_list as users_list
from routes.auth_router import login as login


application = Flask(__name__)
api = Api(application=application, version='0.1', title="Genentech backend",
          description="Genentech backend", validate=True)
bcrypt = Bcrypt(application)
application.config['CORS_HEADERS'] = 'Content-Type'
application.config['CORS_METHODS'] = 'GET,POST,OPTIONS'
# CORS(application, supports_credentials=True)


Arango = ArangoDB(
       hosts=config.ARANGODB_DATABASE_URL
)
Arango.Initialize_database()
api.add_namespace(userApi)
api.add_namespace(users_list)
api.add_namespace(login)
api.init_app(application)


if __name__ == "__main__":
    application.run(debug=True)
