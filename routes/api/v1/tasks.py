import services.Task as TaskService
import services.Job as JobService
from flask_restx import Namespace, Resource
from flask import request, send_file
import services.Utils as Utils
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import tasks, responses
import os

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
    @namespace.doc('tasks/getone', security='Bearer')
    @namespace.response(404, 'Task not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.marshal_with(tasks.a_tasks_response)
    @jwt_required()
    def get(self, id):
        task = TaskService.select(id=id)
        if task is None:
            return {'success': False, 'message': 'task not found', 'data': {}}, 200

        return {'success': True, 'data': task.to_json()}, 200

    @namespace.doc('tasks/updateone', security='Bearer')
    @namespace.marshal_with(tasks.a_tasks_response)
    @namespace.expect(tasks.tasks_model)
    @namespace.response(404, 'Task not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def put(self, id):
        task = TaskService.select(id=id)
        if task is None:
            return {'success': False, 'message': 'task not found', 'data': {}}, 200
        body = request.json
        task = TaskService.update(id=id, data=body)

        return {'success': True, 'data': task.to_json()}, 200

    @namespace.doc('task/delete', security='Bearer')
    @namespace.marshal_with(tasks.a_tasks_response)
    @namespace.response(404, 'task not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def delete(self, id):

        task = TaskService.select(id=id)
        if task is None:
            return {'success': False, 'message': 'task not found', 'data': {}}, 200

        JobService.delete_connection(_to=task._id)
        deleted = TaskService.delete(task.id).to_json()
        return {'success': True, 'data': deleted}, 200


@namespace.route('/im/<id>')
@namespace.param('id', 'task id')
class TasksGetIm(Resource):
    @namespace.doc('tasks/getim', security='Bearer')
    @namespace.response(404, 'Task not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    # @namespace.marshal_with(tasks.a_tasks_response)
    @jwt_required()
    def get(self, id):
        task = TaskService.select(id=id)
        if task is None:
            return {'success': False, 'message': 'task not found', 'data': {}}, 200
        task = task.to_json()
        if task.get('impath') is None:
            return {'success': False, 'message': 'image not found', 'data': {}}, 200

        path = task.get('impath')
        path = Utils.getAbsoluteRelative(path, absolute=True)
        if not os.path.exists(path):
            return {'success': False, 'message': 'image not found', 'data': {}}, 200

        return send_file(path, mimetype='image/png')


@namespace.route('/list')
class TaskListPost(Resource):
    @namespace.doc('tasks/getlist', security='Bearer')
    @namespace.expect(tasks.task_post_model)
    @namespace.marshal_with(tasks.list_tasks_response)
    @namespace.response(404, 'Tasks not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        body = request.json
        tasks = TaskService.select_tasks(condition='in', _key=body['ids'])
        if tasks is None:
            return {'success': False, 'data': []}, 200
        return {'success': True, 'data': tasks}, 200


@namespace.route('')
class TaskPost(Resource):
    @namespace.doc('tasks/update', security='Bearer')
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

    @namespace.doc('task/get', security='Bearer')
    @namespace.marshal_with(tasks.list_tasks_response)
    @namespace.response(200, 'list tasks current user', tasks.list_tasks_response)
    @namespace.response(404, 'tasks not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        result = TaskService.select_tasks(author=author)

        if result is None:
            return {'success': False, 'message': 'tasks not found', 'data': {}}, 200

        return {'success': True, 'data': result}, 200
