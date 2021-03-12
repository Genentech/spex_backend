from flask_restx import Namespace, Resource
from modules.omeroweb import omeroweb
from flask import request, send_file, abort, Response
from .models import responses, omero
import modules.omerodb.model as omerodb
import services.Image as ImageService
import io
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
import datetime
import urllib
from os import getenv


# from os import getenv

namespace = Namespace('Omero', description='Omera operations')
namespace.add_model(omero.omero_tree_model.name, omero.omero_tree_model)
namespace.add_model(omero.omero_thumbnail.name, omero.omero_thumbnail)
namespace.add_model(omero.omero_download_model.name, omero.omero_download_model)
namespace.add_model(omero.login_model.name, omero.login_model)
namespace.add_model(omero.login_responce.name, omero.login_responce)
namespace.add_model(responses.error_response.name, responses.error_response)


def walk_by_structure(item):
    result = {
        'id': item.getId(),
        'type': item.OMERO_CLASS,
        'name': item.getName(),
        'owner': item.getOwnerOmeName(),
        'description': item.getDescription(),
        'date': int(item.getDate().timestamp()*1000),
    }

    try:
        children = []
        for child in item.listChildren():
            children.append(walk_by_structure(child))

        result['children'] = children
    except NotImplementedError:
        pass

    return result


def project_to_json(project):
    if project is None:
        return {}

    return walk_by_structure(project)


@namespace.route('/getProjectTree')
class getProjectTree(Resource):
    @namespace.doc('omero/tree')
    @namespace.expect(omero.omero_tree_model)
    # @namespace.marshal_with(users.a_user_response)
    # @namespace.header('Authorization', 'JWT token')
    # @namespace.response(200, 'List', omero.omero_tree_response)
    @namespace.response(404, 'Connect problems', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    def post(self):
        res = {}
        body = request.json
        conn = omerodb.connect(body['login'], body['password'])
        my_exp_id = conn.getUser().getId()
        default_group_id = conn.getEventContext().groupId
        for project in conn.getObjects("Project", opts={'owner': my_exp_id,
                                                        'group': default_group_id,
                                                        'order_by': 'lower(obj.name)'}):  # , 'limit': 5, 'offset': 0
            res = project_to_json(project)

        omerodb.disconnect(conn)

        return {'success': True, 'data': res}, 200


@namespace.route('/getThumbnail')
class getThumbnail(Resource):
    @namespace.doc('omero/thumbnail')
    @namespace.expect(omero.omero_thumbnail)
    # @namespace.marshal_with(ome.a_user_response)
    # @namespace.header('Authorization', 'JWT token')
    # @namespace.response(200, 'List', users.a_user_response)
    @namespace.response(404, 'Connect problems', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    def post(self):
        body = request.json

        conn = omerodb.connect(body['login'], body['password'])
        rendered_thumb = omerodb.render_thumbnail(body['imageId'], conn, body['size'])
        omerodb.disconnect(conn)

        return send_file(io.BytesIO(rendered_thumb), mimetype='image/png')


@namespace.route('/download')
class downloadFromOmero(Resource):
    @namespace.doc('omero/omero_download')
    @namespace.expect(omero.omero_download_model)
    # @namespace.marshal_with(ome.a_user_response)
    # @namespace.header('Authorization', 'JWT token')
    # @namespace.response(200, 'List', users.a_user_response)
    @namespace.response(404, 'Connect problems', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    def post(self):
        body = request.json
        has_img = ImageService.select(body['imageId'])
        if has_img:
            return {'success': True, 'data': has_img.to_json()}, 200

        conn = omerodb.connect(body['login'], body['password'])
        path = omerodb.saveImage(body['imageId'], conn)
        if path != '':
            result = ImageService.insert({"omeroId": body['imageId'], "path": path})
            return {'success': True, 'data': result.to_json()}, 200
        abort(401, 'Unable to save image')


@namespace.route('/px/<path:path>')
class webGateway(Resource):
    @namespace.doc('omero/px')
    @namespace.response(404, 'Connect problems', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required(locations=['headers'])
    def get(self, path):
        # SITE_NAME = getenv('OMERO_PROXY_PATH') + path
        current_user = get_jwt_identity()
        client = omeroweb.createFind(current_user['login'], current_user['password'])

        pathToReplace = getPath(request)

        parsedurl = urllib.parse.urlparse(getenv('OMERO_PROXY_PATH'))
        port = str(parsedurl.port)
        if port == '0':
            port = ''

        path = request.url.replace(request.host_url + pathToReplace, getenv('OMERO_PROXY_PATH'))

        response = client.get(path)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection', 'Authorization', ]
        headers = [(name, value) for (name, value) in response.raw.headers.items() if name.lower() not in excluded_headers]

        return Response(response.content, response.status_code, headers)


@namespace.route('/login')
class Login(Resource):
    @namespace.doc('omero/login')
    @namespace.expect(omero.login_model)
    @namespace.marshal_with(omero.login_responce)
    @namespace.header('Authorization', 'JWT token')
    @namespace.response(200, 'Logged user', omero.login_responce)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    def post(self):
        body = request.json
        login = body['login']
        password = body['password']
        client = omeroweb.createFind(login, password)
        if client is None:
            abort(401, 'Unable to login user')

        expires = datetime.timedelta(days=7)
        access_token = create_access_token(identity={'login': login, 'password': password}, expires_delta=expires)

        return {'success': True, 'Authorization': access_token}, 200, \
               {'AuthorizationOmero': access_token}


def getPath(request):
    arr = request.url_rule.rule.lower().split('/')
    arr = list(filter(None, arr))
    print(arr)
    index2 = -1
    for item in arr:
        if item.find('<') != -1 or item.find('>') != -1 or item.find(':') != -1:
            index2 = arr.index(item)
            break
    if index2 != -1:
        del arr[index2]
    # if request.environ.get('SERVER_PORT') is not None:
        # arr = [request.environ.get('SERVER_PORT')] + arr
        return '/'.join(arr)
