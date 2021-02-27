from flask_restx import Namespace, Resource
from modules.omeroweb import omeroweb
from flask import request, send_file, abort, Response
from .models import responses, omero
import modules.omerodb.model as omerodb
import services.Image as ImageService
import io
from basicauth import decode
# from flask_jwt_extended import jwt_required


# from os import getenv

namespace = Namespace('Omero', description='Omera operations')
namespace.add_model(omero.omero_tree_model.name, omero.omero_tree_model)
namespace.add_model(omero.omero_thumbnail.name, omero.omero_thumbnail)
namespace.add_model(omero.omero_download_model.name, omero.omero_download_model)
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
    @namespace.header('Authorization', 'Basic')
    # @jwt_required(locations=['headers'])
    def get(self, path):
        # SITE_NAME = getenv('OMERO_PROXY_PATH') + path
        authentication = request.headers['Authorization']
        username, password = decode(authentication)
        omeroweb.createFind(username, password)
        path = request.url.replace('8080/api/v1/omero/px', '4080')
        response = omeroweb.client.get(path)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection', ]
        headers = [(name, value) for (name, value) in response.raw.headers.items() if name.lower() not in excluded_headers]

        return Response(response.content, response.status_code, headers)
