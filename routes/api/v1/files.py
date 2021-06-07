import services.Files as fileService
from flask_restx import Namespace, Resource
from flask import request
from flask_jwt_extended import jwt_required
from .models import files as _file
from .models import responses


namespace = Namespace('Files', description='Files operations CRUD operations')

namespace.add_model(_file.file_model.name, _file.file_model)
namespace.add_model(_file.file_get_model.name, _file.file_get_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(responses.error_response.name, responses.error_response)


@namespace.route('')
class TaskResPost(Resource):
    @namespace.doc('resource/insertone', security='Bearer')
    # @namespace.expect(_resource.task_post_model)
    # @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'resource not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    def post(self):
        body = request.json
        data = dict(body)
        uploaded_files = request.files.getlist("file[]")
        print(uploaded_files)

        # resource = fileService.insert(data=data, collection='resource')

        return {'success': True, 'data': data}, 200
