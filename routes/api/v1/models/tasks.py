from flask_restx import fields, Model
from .responses import response

tasks_model = Model('TasksBase', {
    'name': fields.String,
    'content': fields.String,
    'omeroId': fields.String,
    'parent': fields.String,
    'status': fields.Integer,
    'status_name': fields.String,
    'error': fields.String
})


tasks_data_get_model = Model('TaskDataGetModel', {
    'fields': fields.List(fields.String, required=True, description='data keys')
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

zarr_genes = Model('ZarrGenes', {
    'data': fields.List(fields.String, required=True, description='genes'),
    'clusters': fields.List(fields.Raw),
})