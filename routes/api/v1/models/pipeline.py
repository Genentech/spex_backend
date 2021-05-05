from flask_restx import fields, Model
from .responses import response

pipeline_model = Model('PipelineBase', {
    'name': fields.String,
    'content': fields.String,
    'omeroId': fields.Integer,
    'parent': fields.String,
    'status': fields.Integer
})

pipeline_get_model = pipeline_model.inherit('Pipeline get', {
    'id': fields.String(
        required=True,
        description='pipeline id'
    ),
    'csvdata': fields.Wildcard(fields.List(fields.List(fields.String())))
})

pipeline_post_model = pipeline_model.inherit('Pipeline post', {
    'ids': fields.List(fields.String, required=True, description='pipeline id')
})


list_pipeline_response = response.inherit('PipelineListResponse', {
    'data': fields.List(fields.Nested(pipeline_get_model))
})

a_pipeline_response = response.inherit('PipelineResponse', {
    'data': fields.List(fields.Nested(pipeline_get_model))
})
