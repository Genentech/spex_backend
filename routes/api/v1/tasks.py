import services.Task as TaskService
from flask_restx import Namespace, Resource
from flask import request, abort
# from models.Job import Job
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import tasks, responses

namespace = Namespace('Tasks', description='Tasks CRUD operations')

namespace.add_model(tasks.tasks_model.name, tasks.tasks_model)
namespace.add_model(tasks.task_post_model.name, tasks.task_post_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(tasks.a_tasks_response.name, tasks.a_tasks_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(tasks.list_tasks_response.name, tasks.list_tasks_response)
namespace.add_model(tasks.task_get_model.name, tasks.task_get_model)


@namespace.route('/<id>')
@namespace.param('id', 'task id')
class TaskGetPut(Resource):
    @namespace.doc('tasks/getone')
    @namespace.response(404, 'Task not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.marshal_with(tasks.a_tasks_response)
    @jwt_required()
    def get(self, id):
        task = TaskService.select(id=id)
        if task is None:
            abort(404, 'task not found')

        return {'success': True, 'data': task.to_json()}, 200

    @namespace.doc('tasks/updateone')
    @namespace.marshal_with(tasks.a_tasks_response)
    @namespace.expect(tasks.tasks_model)
    @namespace.response(404, 'Task not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def put(self, id):
        task = TaskService.select(id=id)
        if task is None:
            abort(404, 'task not found')
        body = request.json
        task = TaskService.update(id=id, data=body)

        return {'success': True, 'data': task.to_json()}, 200


@namespace.route('/')
class TaskPost(Resource):
    @namespace.doc('tasks/update')
    @namespace.expect(tasks.task_post_model)
    @namespace.marshal_with(tasks.list_tasks_response)
    @namespace.response(404, 'Task not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        body = request.json
        arr = []
        for id in body['ids']:
            data = dict(body)
            del data['ids']
            task = TaskService.update(id=id, data=data)
            if task is not None:
                arr.append(task.to_json())
        return {'success': True, 'data': arr}, 200

    @namespace.doc('task/get')
    @namespace.marshal_with(tasks.list_tasks_response)
    @namespace.response(200, 'list tasks current user', tasks.list_tasks_response)
    @namespace.response(404, 'tasks not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        result = TaskService.select_tasks(author=author)

        if result is None:
            abort(404, 'tasks not found')

        return {'success': True, 'data': result}, 200
