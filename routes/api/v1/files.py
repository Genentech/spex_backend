from typing import Collection
import services.Files as fileService
from flask_restx import Namespace, Resource
from flask import request
from flask_jwt_extended import jwt_required
from .models import files as _file
from .models import responses
from werkzeug.datastructures import FileStorage
import os


namespace = Namespace('Files', description='Files operations CRUD operations')
upload_parser = namespace.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True)

namespace.add_model(_file.file_model.name, _file.file_model)
namespace.add_model(_file.file_get_model.name, _file.file_get_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(responses.error_response.name, responses.error_response)


# @namespace.param('filenames', _in='files', description='Upload multiple files', required=True, type='array', items={'type': 'file'}, collectionFormat='multi')
@namespace.route('')
class TaskResPost(Resource):
    @namespace.doc('resource/insertone', security='Bearer')
    @namespace.expect(upload_parser)
    # @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'resource not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    def post(self):
        args = upload_parser.parse_args()
        file = args['file']
        destination = os.path.join(os.getenv('UPLOAD_FOLDER')) + '\\'
        if not os.path.exists(destination):
            os.makedirs(destination)
        xls_file = '%s%s' % (destination, 'custom_file_name.ico')
        file.save(xls_file)

        return {'success': 'True'}, 200
