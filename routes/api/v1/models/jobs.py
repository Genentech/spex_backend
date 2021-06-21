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
        fields.Integer,
        required=True,
        description='image id'),
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
