from flask_restx import Api
from werkzeug.exceptions import HTTPException
from .users import namespace as users
from .omero import namespace as omero

api = Api(
    version='1.0',
    title='Genentech API',
    description='Genentech API',
    validate=True,
)

prefix = '/api/v1'


@api.errorhandler
@api.errorhandler(Exception)
@api.errorhandler(HTTPException)
def default_error_handler(error):
    code = getattr(error, 'code', 500)
    result = {
        'success': False,
        'code': code,
        'message': getattr(error, 'description', str(error))
    }
    return result, code


api.add_namespace(users, '{}/users'.format(prefix))
api.add_namespace(omero, '{}/omero'.format(prefix))
