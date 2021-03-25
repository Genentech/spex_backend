import datetime
from flask import Blueprint
from flask_jwt_extended import unset_jwt_cookies, set_access_cookies
from .api.v1 import api as api_v1

blueprint = Blueprint('root', __name__, url_prefix='/v1')


@blueprint.after_request
def after_request(response):

    if response.status_code == 401:
        unset_jwt_cookies(response)
        return response

    token = response.headers.get('Authorization')
    if token:
        set_access_cookies(response, token, datetime.timedelta(days=7))

    return response


api_v1.init_app(blueprint)
