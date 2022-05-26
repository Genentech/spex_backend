from flask import url_for, request
from flask_restx import Api, apidoc
from urllib import parse
from werkzeug.exceptions import HTTPException
from .users import namespace as users
from .omero import namespace as omero
from .jobs import namespace as jobs
from .tasks import namespace as tasks
from .resource import namespace as resource
from .projects import namespace as projects
from .pipeline import namespace as pipeline
from .images import namespace as images
from .files import namespace as files
from .history import namespace as history
from .templates import namespace as templates


class OverrideApi(Api):
    @property
    def specs_url(self):
        specs_url = super(OverrideApi, self).specs_url
        origin = request.headers.get_all('X-Original-Request')

        if len(origin) > 0:
            origin = f'{origin[0]}swagger.json'

        return origin if origin else specs_url


prefix = ''

authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token"
    }
}

api = OverrideApi(
    version='1.0',
    title='Genentech API',
    description='Genentech API',
    validate=True,
    security='Bearer Auth',
    authorizations=authorizations
)


@apidoc.apidoc.add_app_template_global
def swagger_static(filename):
    path = url_for("restx_doc.static", filename=filename)

    url = parse.urlparse(request.url)
    sub_path = url_for(api.endpoint("root"), _external=False)

    if url.path == sub_path:
        return f'..{path}'

    return path


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
api.add_namespace(jobs,  '{}/jobs'.format(prefix))
api.add_namespace(tasks, '{}/tasks'.format(prefix))
api.add_namespace(resource, '{}/resource'.format(prefix))
api.add_namespace(projects, '{}/projects'.format(prefix))
api.add_namespace(pipeline, '{}/pipeline'.format(prefix))
api.add_namespace(images, '{}/images'.format(prefix))
api.add_namespace(files, '{}/files'.format(prefix))
api.add_namespace(history, '{}/history'.format(prefix))
api.add_namespace(templates, '{}/templates'.format(prefix))
