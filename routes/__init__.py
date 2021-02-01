from flask import Blueprint
from .api.v1 import api as api_v1

blueprint = Blueprint('root', __name__, url_prefix='/')

api_v1.init_app(blueprint)
