import services.Job as JobService
from flask_restx import Namespace, Resource
from flask import request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import resource as _resource
from .models import responses


namespace = Namespace('Resource', description='Tasks-jobs-box-result CRUD operations')

namespace.add_model(_resource.tasks_model.name, _resource.tasks_model)
namespace.add_model(_resource.task_post_model.name, _resource.task_post_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(_resource.a_tasks_response.name, _resource.a_tasks_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(_resource.list_tasks_response.name, _resource.list_tasks_response)
namespace.add_model(_resource.task_get_model.name, _resource.task_get_model)


# task result
@namespace.route('/<id>')
@namespace.param('id', 'resource id')
class TaskResGetPut(Resource):
    @namespace.doc('resource/getone', security='Bearer')
    @namespace.response(404, 'Resource not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.marshal_with(_resource.a_tasks_response)
    @jwt_required()
    def get(self, id):
        task = JobService.select(id=id, collection='resource')
        if task is None:
            abort(404, 'resource not found')

        return {'success': True, 'data': task.to_json()}, 200

    @namespace.doc('resource/updateone', security='Bearer')
    @namespace.marshal_with(_resource.a_tasks_response)
    @namespace.expect(_resource.tasks_model)
    @namespace.response(404, 'resource not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def put(self, id):
        task = JobService.select(id=id)
        if task is None:
            abort(404, 'resource not found')
        body = request.json
        task = JobService.update(id=id, data=body, collection='resource')

        return {'success': True, 'data': task.to_json()}, 200


@namespace.route('')
class TaskResPost(Resource):
    @namespace.doc('resource/updatemany', security='Bearer')
    @namespace.expect(_resource.task_post_model)
    @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'resource not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        body = request.json
        arr = []
        for id in body['ids']:
            data = dict(body)
            del data['ids']
            resource = JobService.update(id=id, data=data, collection='resource')
            if resource is not None:
                arr.append(resource.to_json())
        return {'success': True, 'data': arr}, 200

    @namespace.doc('resource/getmany', security='Bearer')
    @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(200, 'list resource current user', _resource.list_tasks_response)
    @namespace.response(404, 'resource not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        result = JobService.select_jobs(author=author, collection="resource")

        if result is None:
            abort(404, 'resource not found')

        return {'success': True, 'data': result}, 200
