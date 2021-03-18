import services.Task as TaskService
from flask_restx import Namespace, Resource
from flask import request, abort
# from models.Job import Job
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import tasks, responses

namespace = Namespace('Tasks', description='Tasks CRUD operations')

namespace.add_model(tasks.tasks_model.name, tasks.tasks_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(tasks.a_tasks_response.name, tasks.a_tasks_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(tasks.list_tasks_response.name, tasks.list_tasks_response)
namespace.add_model(tasks.task_get_model.name, tasks.task_get_model)


@namespace.route('/')
class TasksCreateGetPost(Resource):
    @namespace.doc('task/create')
    @namespace.expect(tasks.tasks_model)
    @namespace.response(200, 'Created job', tasks.a_tasks_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        body = request.json
        body['author'] = get_jwt_identity()
        result = TaskService.insert(body)
        return {'success': True, 'data': result.to_json()}, 200

    @namespace.doc('task/get')
    @namespace.response(200, 'list tasks current user', tasks.list_tasks_response)
    @namespace.response(404, 'tasks not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        result = TaskService.select_tasks(author)

        if result is None:
            abort(404, 'tasks not found')

        return {'success': True, 'data': result}, 200
