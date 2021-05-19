from flask_restx import fields, Model
from .responses import response

pipeline_model = Model('PipelineBase', {
    'child_ids': fields.List(fields.String(required=True, description='task or job or another collectiond id that we connect to pipe'), required=True)
})

box_model = Model('BoxBase', {
    'name': fields.String(required=True, description='empty box name')
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
