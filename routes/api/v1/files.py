# from models.Files import file
import os
import services.Files as fileService
from flask_restx import Namespace, Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import files as _file
from .models import responses
from werkzeug.datastructures import FileStorage
import services.Utils as Utils


namespace = Namespace('Files', description='Files operations CRUD operations')
upload_parser = namespace.parser()
upload_parser.add_argument('filenames', location='files', type=FileStorage, required=True)
upload_parser.add_argument('folder', help='parent folder name create if not exist', location='headers', type=str, required=False)

namespace.add_model(_file.file_model.name, _file.file_model)
namespace.add_model(_file.file_get_model.name, _file.file_get_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(responses.error_response.name, responses.error_response)


# TODO @namespace.param(name='filenames', _in='formData', description='Upload file', required=True, type='array', items={'type': 'file'}, collectionFormat='multi') multi uploading

@namespace.route('')
class TaskResPost(Resource):
    @namespace.doc('resource/uploadone', security='Bearer')
    @namespace.expect(upload_parser)
    # @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        args = upload_parser.parse_args()
        file = args['filenames']
        destination = fileService.user_folder(author=get_jwt_identity(), folder=args['folder'])
        filetosave = '%s%s' % (destination, file.filename)
        file.save(filetosave)

        return {'success': 'True', 'filename': file.filename}, 200

    @namespace.doc('resource/getfiletree', security='Bearer')
    # @namespace.expect(upload_parser)
    # @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):

        tree = fileService.path_to_dict(fileService.user_folder(author=get_jwt_identity()))
        return {'success': 'True', 'tree': tree}, 200

    @namespace.doc('resource/deletefilefolder', security='Bearer')
    # @namespace.expect(upload_parser)
    # @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.param('path', 'path to detele')
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
