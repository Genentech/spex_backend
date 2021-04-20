import services.Project as ProjectService
from flask_restx import Namespace, Resource
from flask import request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import projects, responses

namespace = Namespace('Projects', description='Projects CRUD operations')

namespace.add_model(projects.projects_model.name, projects.projects_model)
namespace.add_model(projects.project_get_model.name, projects.project_get_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(projects.a_project_response.name, projects.a_project_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(projects.list_projects_response.name, projects.list_projects_response)


@namespace.route('/')
class ProjectsCreateGetPost(Resource):
    @namespace.doc('projects/create')
    @namespace.expect(projects.projects_model)
    @namespace.marshal_with(projects.a_project_response)
    @namespace.response(200, 'Created project', projects.a_project_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        body = request.json
        body['author'] = get_jwt_identity()
        result = ProjectService.insert(body)
        return {'success': True, 'data': result}, 200

    @namespace.doc('project/get')
    @namespace.marshal_with(projects.list_projects_response)
    @namespace.response(200, 'list projects current user', projects.list_projects_response)
    @namespace.response(404, 'projects not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        result = ProjectService.select_projects(author=author)

        if result is None:
            abort(404, 'projects not found')

        return {'success': True, 'data': result}, 200


@namespace.route('/<string:id>')
class ProjectGetById(Resource):
    @namespace.doc('project/getbyid')
    @namespace.marshal_with(projects.a_project_response)
    @namespace.response(200, 'project by id', projects.a_project_response)
    @namespace.response(404, 'projects not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self, id):
        author = get_jwt_identity()
        result = ProjectService.select_projects(_key=id, author=author)  # only author projects show

        if result is None:
            abort(404, 'projects not found')

        return {'success': True, 'data': result[0]}, 200

    @namespace.doc('project/updateone')
    @namespace.marshal_with(projects.a_project_response)
    # @namespace.expect(projects.projects_model)
    @namespace.response(404, 'Project not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def put(self, id):
        author = get_jwt_identity()
        project = ProjectService.select_projects(_key=id, author=author)   # only author projects show
        if project is None:
            abort(404, 'project not found')
        body = request.json
        project = ProjectService.update(id=id, data=body)

        return {'success': True, 'data': project.to_json()}, 200

    @namespace.doc('project/deleteone')
    @namespace.marshal_with(projects.a_project_response)
    # @namespace.expect(projects.projects_model)
    @namespace.response(404, 'Project not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def delete(self, id):
        author = get_jwt_identity()
        project = ProjectService.select_projects(_key=id, author=author)   # only author projects show
        if project is None:
            abort(404, 'project not found')
        project = ProjectService.delete(_key=id)

        return {'success': True, 'data': project.to_json()}, 200
