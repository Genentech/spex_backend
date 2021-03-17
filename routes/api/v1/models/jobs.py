from flask_restx import fields, Model
from .responses import response

jobs_model = Model('JobsBase', {
    'name': fields.String,
    'content': fields.String,
    'id': fields.List(fields.String)
})

a_jobs_response = response.inherit('JobsResponse', {
    'data': fields.Nested(jobs_model)
})

list_jobs_response = response.inherit('JobsListResponse', {
    'data': fields.List(fields.Nested(jobs_model))
})
