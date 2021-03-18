from flask_restx import fields, Model
from .responses import response

tasks_model = Model('TasksBase', {
    'name': fields.String,
    'content': fields.String,
    'omeroId': fields.Integer,
    'parent': fields.String,
    'status': fields.Integer
})

a_tasks_response = response.inherit('TasksResponse', {
    'data': fields.Nested(tasks_model)
})

task_get_model = tasks_model.inherit('Task get', {
    'id': fields.String(
        required=True,
        description='User id'
    )
})


list_tasks_response = response.inherit('TaskListResponse', {
    'data': fields.List(fields.Nested(task_get_model))
})
