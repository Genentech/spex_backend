from flask_restx import fields, Model
from .responses import response

tasks_model = Model('TasksBase', {
    'name': fields.String,
    'content': fields.String,
    'omeroId': fields.String,
    'parent': fields.String,
    'status': fields.Integer,
    'status_name': fields.String,
})

task_get_model = tasks_model.inherit('Task get', {
    'id': fields.String(
        required=True,
        description='Task id'
    ),
    'csvdata': fields.Wildcard(fields.List(fields.List(fields.String()))),
    'params': fields.Wildcard(fields.Wildcard(fields.String)),

})

task_post_model = Model('TasksList', {
    'ids': fields.List(fields.String, required=True, description='Task id')
})


list_tasks_response = response.inherit('TaskListResponse', {
    'data': fields.Nested(task_get_model, as_list=True)
})

a_tasks_response = response.inherit('TasksResponse', {
    'data': fields.Nested(task_get_model)
})
