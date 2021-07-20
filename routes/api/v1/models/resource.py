from flask_restx import fields, Model
from .responses import response

tasks_model = Model('TasksBase', {
    'name': fields.String,
    'content': fields.String,
    'omeroId': fields.Integer(required=False),
    'omeroIds': fields.List(fields.Integer(required=False)),
    'parent': fields.String,
    'status': fields.Integer
})

task_get_model = tasks_model.inherit('Task get', {
    'id': fields.String(
        required=True,
        description='Task id'
    ),
    'csvdata': fields.Wildcard(fields.List(fields.List(fields.String())))
})

task_post_model = tasks_model.inherit('Task post', {
    'ids': fields.List(fields.String, required=True, description='Task id')
})


list_tasks_response = response.inherit('TaskListResponse', {
    'data': fields.List(fields.Nested(task_get_model))
})

a_tasks_response = response.inherit('TasksResponse', {
    'data': fields.List(fields.Nested(task_get_model))
})
