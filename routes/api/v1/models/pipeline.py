from flask_restx import fields, Model
from .responses import response

pipeline_model = Model('PipelineBase', {
    'name': fields.String(
        description='pipeline name',
        required=False
    ),
    'id': fields.String(
        required=False,
        description='id'
    ),
    'status': fields.Integer(
        required=False,
        description='status'
    ),
    'project': fields.String(
        required=False,
        description='project id'
    )
})


pipeline_get_model = pipeline_model.inherit('Pipeline get', {
    '_id': fields.String(
        required=True,
        description='pipeline db id'
    )
})

task_resource_image_connect_to_box = pipeline_model.inherit('Connect post', {
    'tasks_ids': fields.List(fields.String(required=False, description='task to connect into box')),
    'box_ids': fields.List(fields.String(required=False, description='box ids to connect pipeline')),
    'resource_ids': fields.List(fields.String(required=False, description='resource ids to connect into box'))
})

pipeline_post_model = pipeline_model.inherit('Pipeline post', {
    'ids': fields.List(fields.String, required=True, description='pipeline id')
})


list_pipeline_response = response.inherit('PipelineListResponse', {
    'data': fields.List(fields.Nested(pipeline_get_model))
})

a_pipeline_response = response.inherit('PipelineResponse', {
    'data': fields.Nested(pipeline_get_model)
})
