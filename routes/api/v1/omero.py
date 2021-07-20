import modules.omeroweb as omeroweb
from flask_restx import Namespace, Resource
from flask import request, abort, Response
from .models import responses, omero
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.Cache import CacheService
from datetime import datetime, timedelta
from os import getenv
from urllib.parse import unquote
from services.Utils import download_file


namespace = Namespace('Omero', description='Omero operations')
namespace.add_model(omero.omero_download_model.name, omero.omero_download_model)
namespace.add_model(omero.login_model.name, omero.login_model)
namespace.add_model(omero.login_responce.name, omero.login_responce)
namespace.add_model(responses.error_response.name, responses.error_response)

excluded_headers = [
    # 'content-encoding',
    # 'content-length',
    # 'transfer-encoding',
    # 'connection',
    'set-cookie',
    'authorization'
]


def _request(path, method='get', **kwargs):
    current_user = get_jwt_identity()

    client = omeroweb.get(current_user['login'])
    path = unquote(path)

    if client is None:
        abort(401, 'Unauthorized')
    try:
        index = request.url.index(path) - 1
        path = request.url[index:]
    except ValueError:
        pass

    method = getattr(client, method)

    response = method(path, **kwargs)

    headers = [
        (name, value)
        for (name, value) in response.raw.headers.items()
        if name.lower() not in excluded_headers
    ]

    session = omeroweb.OmeroSession(
        client.omero_session_id,
        client.omero_token,
        client.omero_context,
        datetime.now() + timedelta(hours=int(getenv('MEMCACHED_SESSION_ALIVE_H')))
    )
    CacheService.set(current_user['login'], session)

    return Response(response.content, response.status_code, headers)


@namespace.route('/<path:path>')
class WebGateway(Resource):
    @namespace.doc('omero', security='Bearer')
    @namespace.response(404, 'Connect problems', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required(locations=['headers', 'cookies'])
    def get(self, path):
        return _request(path)

    @namespace.doc('omero', security='Bearer')
    @namespace.response(404, 'Connect problems', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required(locations=['headers', 'cookies'])
    def post(self, path):
        return _request(path, 'post')


@namespace.route('/<string:imageId>')
class DownloadImageReturnPath(Resource):
    @namespace.doc('omero/ImageDownload', security='Bearer')
    @namespace.response(404, 'Connect problems', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self, imageId, format='tif'):
        author = get_jwt_identity()['login']
        session = omeroweb.get(author)
        path = getenv('OMERO_PROXY_PATH') + '/webclient/render_image_download/' + str(imageId) + '/?format=' + format
        relativePath = download_file(path, client=session, imgId=imageId)
        if relativePath is not None:
            return {'success': True, 'path': relativePath}, 200
