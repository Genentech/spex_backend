from flask_restx import Namespace, Resource
from flask import request, send_file, abort
from .models import responses, omero
import modules.omerodb.model as omerodb
import io


namespace = Namespace('Omero', description='Omera operations')
namespace.add_model(omero.omero_tree_model.name, omero.omero_tree_model)
namespace.add_model(omero.omero_thumbnail.name, omero.omero_thumbnail)
namespace.add_model(omero.omero_download_model.name, omero.omero_download_model)
namespace.add_model(responses.error_response.name, responses.error_response)


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
        res = []
        body = request.json
        conn = omerodb.connect(body['login'], body['password'])
        my_exp_id = conn.getUser().getId()
        default_group_id = conn.getEventContext().groupId
        for project in conn.getObjects("Project", opts={'owner': my_exp_id,
                                                        'group': default_group_id,
                                                        'order_by': 'lower(obj.name)',
                                                        'limit': 5, 'offset': 0}):
            res.append(omerodb.returnObj(project))
            # We can get Datasets with listChildren, since we have the Project already.
            # Or conn.getObjects("Dataset", opts={'project', id}) if we have Project ID
            for dataset in project.listChildren():
                res.append(omerodb.returnObj(dataset, 2))
                for image in dataset.listChildren():
                    res.append(omerodb.returnObj(image, 4))

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
        conn = omerodb.connect(body['login'], body['password'])
        path = omerodb.saveImage(body['imageId'], conn)
        if path != '':
            return {'success': True, 'path': path}, 200
        abort(401, 'Unable to save image')
