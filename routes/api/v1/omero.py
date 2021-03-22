import modules.omeroweb as omeroweb
from flask_restx import Namespace, Resource
from flask import request, abort, Response
from .models import responses, omero
from flask_jwt_extended import jwt_required, get_jwt_identity


namespace = Namespace('Omero', description='Omera operations')
namespace.add_model(omero.login_model.name, omero.login_model)
namespace.add_model(omero.login_responce.name, omero.login_responce)
namespace.add_model(responses.error_response.name, responses.error_response)

excluded_headers = [
    'content-encoding',
    'content-length',
    'transfer-encoding',
    'connection',
    'Authorization'
]


def _request(path, method='get', **kwargs):
    current_user = get_jwt_identity()

    client = omeroweb.get(current_user['login'])

    if client is None:
        abort(401, 'Unauthorized')

    index = request.url.index(path) - 1

    path = request.url[index:]

    method = getattr(client, method)

    response = method(path, **kwargs)

    headers = [
        (name, value)
        for (name, value) in response.raw.headers.items()
        if name.lower() not in excluded_headers
    ]

    return Response(response.content, response.status_code, headers)


@namespace.route('/<path:path>')
class WebGateway(Resource):
    @namespace.doc('omero')
    @namespace.response(404, 'Connect problems', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required(locations=['headers'])
    def get(self, path):
        return _request(path)

    @namespace.doc('omero')
    @namespace.response(404, 'Connect problems', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required(locations=['headers'])
    def post(self, path):
        return _request(path, 'post')
