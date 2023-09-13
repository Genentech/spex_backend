import spex_common.services.Project as ProjectService
import spex_common.services.Pipeline as PipelineService
import spex_common.services.Job as JobService
import spex_common.services.Task as TaskService
from flask_restx import Namespace, Resource, reqparse
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import projects, responses
from spex_common.models.Status import TaskStatus


namespace = Namespace("Projects", description="Projects CRUD operations")
namespace.add_model(projects.author_model.name, projects.author_model)
namespace.add_model(projects.projects_model.name, projects.projects_model)
namespace.add_model(projects.project_get_model.name, projects.project_get_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(projects.a_project_response.name, projects.a_project_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(
    projects.list_projects_response.name, projects.list_projects_response
)
parser = reqparse.RequestParser()



@namespace.route("")
class ProjectsCreateGetPost(Resource):
    @namespace.doc("projects/create", security="Bearer")
    @namespace.expect(projects.projects_model)
    @namespace.marshal_with(projects.a_project_response)
    @namespace.response(200, "Created project", projects.a_project_response)
    @namespace.response(400, "Message about reason of error", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @jwt_required()
    def post(self):
        body = request.json
        body["author"] = get_jwt_identity()
        result = ProjectService.insert(body)
        return {"success": True, "data": result}, 200

    @namespace.doc("project/get", security="Bearer")
    @namespace.marshal_with(projects.list_projects_response)
    @namespace.response(
        200, "list projects current user", projects.list_projects_response
    )
    @namespace.response(404, "projects not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        result = ProjectService.select_projects(author=author)

        if result is None:
            return {"success": True, "data": []}, 200
        for project in result:
            project["author"] = dict(project["author"])

        return {"success": True, "data": result}, 200


@namespace.route("/<string:id>")
class ProjectGetById(Resource):
    @namespace.doc("project/getbyid", security="Bearer")
    @namespace.marshal_with(projects.a_project_response)
    @namespace.response(200, "project by id", projects.a_project_response)
    @namespace.response(404, "projects not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @jwt_required()
    def get(self, id):
        author = get_jwt_identity()
        result = ProjectService.select_projects(
            _key=id, author=author
        )  # only author projects show

        if result is None:
            return {"success": False, "message": "project not found"}, 404
        project = result[0]
        project["author"] = dict(project["author"])

        return {"success": True, "data": project}, 200

    @namespace.doc("project/updateone", security="Bearer")
    @namespace.marshal_with(projects.a_project_response)
    @namespace.expect(projects.projects_model)
    @namespace.response(404, "Project not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @jwt_required()
    def put(self, id):
        author = get_jwt_identity()
        project = ProjectService.select_projects(
            _key=id, author=author
        )  # only author projects show
        if project is None:
            return {"success": False, "message": "project not found"}, 404
        body = request.json
        project = ProjectService.update(id=id, data=body)

        return {"success": True, "data": project.to_json()}, 200

    @namespace.doc("project/deleteone", security="Bearer")
    @namespace.marshal_with(projects.a_project_response)
    @namespace.response(404, "Project not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @jwt_required()
    def delete(self, id):
        author = get_jwt_identity()
        project = ProjectService.select_projects(
            _key=id, author=author
        )  # only author projects show
        if project is None:
            return {"success": False, "message": "project not found"}, 404

        project = ProjectService.delete(_key=id)

        return {"success": True, "data": project.to_json()}, 200


parser.add_argument('pipeline_id', type=str, required=False)


@namespace.route("/<string:id>/list")
class ProjectGetById(Resource):
    @namespace.doc("project/getbyid", security="Bearer")
    # @namespace.marshal_with(projects.a_project_response)
    @namespace.response(200, "project by id", projects.a_project_response)
    @namespace.response(404, "projects not found", responses.error_response)
    @namespace.response(401, "Unauthorized", responses.error_response)
    @jwt_required()
    def get(self, id):
        author = get_jwt_identity()
        args = parser.parse_args()
        condition: dict = {
            "project": id,
            "author": author,
            "collection": "pipeline",
        }
        if args['pipeline_id']:
            condition['_key'] = args['pipeline_id']

        result = PipelineService.select_pipeline(**condition)
        if not result:
            return {"success": False, "message": "project not found"}, 404

        res = []
        for pipeline in result:
            pipelines = PipelineService.get_tree(pipeline_id=pipeline["id"])
            jobs_list = PipelineService.get_jobs(pipelines, prefix=False)
            task_that_we_can_wiz = ('feature_extraction', 'transformation', 'cluster', 'dml')
            if jobs := JobService.select_jobs(condition=" in ", _key=jobs_list):
                jobs = [
                    job
                    for job in jobs
                    if job["name"] in task_that_we_can_wiz
                    and job["status_name"] == TaskStatus.complete.name
                ]
                if jobs:
                    for job in jobs:
                        job["tasks"] = TaskService.select_tasks(parent=job["id"])
                    pipeline["jobs"] = jobs
                    res.append(pipeline)
        if res is None:
            return {"success": False, "message": "project not found"}, 404

        return {"success": True, "data": res}, 200
