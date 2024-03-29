from flask_restx import fields, Model
from .responses import response
from spex_common.models.Status import PipelineStatus

pipeline_create_model = Model('PipelineBase', {
    'name': fields.String(
        description='pipeline name',
        required=True
    )
})


pipeline_copy_model = Model('PipelineBase', {
    'parent_id': fields.String(
        description='pipeline id',
        required=True
    ),
    'name': fields.String(
        description='pipeline name',
        required=False
    )
})

pipeline_model = pipeline_create_model.inherit('Pipeline base1', {
    'id': fields.String(
        required=False,
        description='id'
    ),
    'status': fields.Integer(
        required=False,
        description='status'
    ),
    'status_name': fields.String,
    'shared': fields.Boolean(
        required=False,
        description='shared to other users'
    ),
    'project': fields.String(
        required=False,
        description='project id'
    )
})

shared_pipeline = Model('PipelineShared', {
    'shared': fields.Boolean(
        required=False,
        description='shared to other users'
    ),

})

pipeline_get_model = pipeline_model.inherit('Pipeline get', {
    '_id': fields.String(
        required=True,
        description='pipeline db id'
    )
})

task_resource_image_connect_to_job = pipeline_model.inherit('Connect post', {
    'tasks_ids': fields.List(fields.String(required=False, description='task to connect into job')),
    'job_ids': fields.List(fields.String(required=False, description='job ids to connect pipeline')),
    'resource_ids': fields.List(fields.String(required=False, description='resource ids to connect into job'))
})

pipeline_post_model = pipeline_model.inherit('Pipeline post', {
    'ids': fields.List(fields.String, required=True, description='pipeline id')
})


list_pipeline_response = response.inherit('PipelineListResponse', {
    'data': fields.List(fields.Nested(pipeline_get_model))
})

a_pipeline_response = response.inherit('PipelineResponse', {
    'data': fields.Nested(pipeline_get_model, required=False),
    'message': fields.String(required=False, description='error reason')
})


pipeline_status_model = Model('PipelineStatus', {
    'status': fields.String(
        description='pipeline name',
        required=True,
        enum=PipelineStatus._member_names_
    )
})
