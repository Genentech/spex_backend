from flask_restx import fields, Model
from .responses import response

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
        fields.Integer,
        required=False,
        description='image id'),
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
