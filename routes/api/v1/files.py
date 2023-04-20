# from models.Files import file
import os
import spex_common.services.Files as fileService
from flask_restx import Namespace, Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import files as _file
from .models import responses
from werkzeug.datastructures import FileStorage
import spex_common.services.Utils as Utils
import anndata


namespace = Namespace('Files', description='Files operations CRUD operations')
upload_parser = namespace.parser()
upload_parser.add_argument('filenames', location='files', type=FileStorage, required=True)
upload_parser.add_argument('folder', help='parent folder name create if not exist', location='headers', type=str, required=False)

namespace.add_model(_file.file_model.name, _file.file_model)
namespace.add_model(_file.file_get_model.name, _file.file_get_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(responses.error_response.name, responses.error_response)


#  TODO @namespace.param(name='filenames', _in='formData', description='Upload file',
#   required=True, type='array', items={'type': 'file'}, collectionFormat='multi') multi uploading

@namespace.route('')
class FileResPost(Resource):
    @namespace.doc('file/uploadone', security='Bearer')
    @namespace.expect(upload_parser)
    # @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        args = upload_parser.parse_args()
        file = args['filenames']
        destination = fileService.user_folder(author=get_jwt_identity(), folder=args['folder'])
        file_to_save = os.path.join(destination, file.filename)
        file.save(file_to_save)

        return {'success': 'True', 'filename': file.filename}, 200

    @namespace.doc('file/getfiletree', security='Bearer')
    # @namespace.expect(upload_parser)
    # @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):

        tree = fileService.path_to_dict(fileService.user_folder(author=get_jwt_identity()))
        return {'success': 'True', 'tree': tree}, 200

    @namespace.doc('file/deletefilefolder', security='Bearer')
    # @namespace.expect(upload_parser)
    # @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.param('path', 'path to delete')
    @jwt_required()
    def delete(self):

        path = request.args.get('path')

        _path, folder = fileService.check_path(get_jwt_identity(), path)
        if _path is None:
            return {'success': False, 'message': f'path {path} not found'}, 200
        else:
            if folder:
                Utils._rmDir(_path)
            else:
                os.remove(_path)

        return {'success': True, 'deleted': path}, 200


@namespace.route('/check-file')
class CheckFileResource(Resource):
    @namespace.doc('file/check', security='Bearer')
    @namespace.response(404, 'File not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.param('filename', 'Filename to check')
    @jwt_required()
    def get(self):
        filename = request.args.get('filename')
        if not filename:
            return {'success': False, 'message': 'Filename parameter is required'}, 400

        user_folder = fileService.user_folder(author=get_jwt_identity())
        file_path = os.path.join(user_folder, filename)

        if not os.path.exists(file_path):
            return {'success': False, 'message': f'File {filename} not found'}, 404

        try:
            adata = anndata.read_h5ad(file_path)
            keys = list(adata.obs_keys())
            return {'success': True, 'keys': keys}, 200
        except Exception as e:
            return {'success': False, 'message': f'Error processing file: {str(e)}'}, 500
