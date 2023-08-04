from flask_restx import fields, Model
from .responses import response

author_model = Model('Author', {
    'id': fields.String,
    'login': fields.String,
})

projects_model = Model('ProjectBase', {
    'name': fields.String(
        required=True,
        description='Project name'
    ),
    'description': fields.String(
        required=False,
        description='long description'
    ),
    'omeroIds': fields.List(
        fields.String,
        required=False,
        description='image id'),
    'file_names': fields.List(
        fields.String,
        required=False,
        description='file attached names'),
    'taskIds': fields.List(
        fields.String,
        required=False,
        description='Tasks id'),
    'resource_ids': fields.List(
        fields.String,
        required=False,
        description='Tasks results (resource)id'),
    'author': fields.Nested(author_model),
})


project_get_model = projects_model.inherit('ProjectsGet', {
    'id': fields.String(
        required=True,
        description='User id'
    )
})


a_project_response = response.inherit('ProjectResponse', {
    'data': fields.Nested(project_get_model)
})

list_projects_response = response.inherit('ProjectsListResponse', {
    'data': fields.List(fields.Nested(project_get_model))
})
