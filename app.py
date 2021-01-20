from flask import Flask
# from routes.auth_router import auth, login_bp
# from database.db import Initialize_database
from flask_restx import Api
# from flask_cors import CORS
from routes.auth_router import register as userApi
from routes.auth_router import users_list as users_list


application = Flask(__name__)
api = Api(application=application, version='0.1', title="Genentech backend",
          description="Genentech backend", validate=True)
application.config['CORS_HEADERS'] = 'Content-Type'
application.config['CORS_METHODS'] = 'GET,POST,OPTIONS'
# CORS(application, supports_credentials=True)

# Initialize_database()
api.add_namespace(userApi)
api.add_namespace(users_list)
api.init_app(application)


if __name__ == "__main__":
    application.run(debug=True)
