from flask_restx import fields, Model
from .responses import response
from .tasks import task_get_model

jobs_model = Model('JobBase', {
    'name': fields.String(
        required=True,
        description='job name'
    ),
    'content': fields.String(
        required=True,
        description='That we do'
    ),
    'omeroIds': fields.List(
        fields.String,
        required=False,
        description='image id'),
    'status': fields.Integer(
        requred=False,
        description='status'),
    'status_name': fields.String,
})

jobs_update_model = Model('JobUpdate', {
    'name': fields.String(
        description='job name',
        required=False,
    ),
    'content': fields.String(
        description='That we do',
        required=False,
    ),
    'omeroIds': fields.List(
        fields.String,
        required=False,
        description='image id'),
    'status': fields.Integer(
        requred=False,
        description='status'),
})

jobs_status_update_model = Model('JobStatusUpdate', {
    'status': fields.Integer(
        requred=False,
        description='status'),
})


job_get_model = jobs_model.inherit('JobsGet', {
    'id': fields.String(
        required=True,
        description='Job id'
    ),
    'tasks': fields.List(fields.Nested(task_get_model)),
})

list_jobs_response = response.inherit('JobsListResponse', {
    'data': fields.Nested(job_get_model, as_list=True),
})


a_jobs_response = response.inherit('JobsResponse', {
    'data': fields.Nested(job_get_model),
})

a_jobs_type_response = response.inherit('JobsResponse', {
    'data': fields.List(fields.String(required=True, description='Job type name')),
})
