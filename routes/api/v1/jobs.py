import services.Job as JobService
import services.Task as TaskService
from flask_restx import Namespace, Resource
from flask import request, abort
# from models.Job import Job
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import jobs, responses

namespace = Namespace('Jobs', description='Jobs CRUD operations')

namespace.add_model(jobs.jobs_model.name, jobs.jobs_model)
namespace.add_model(jobs.job_get_model.name, jobs.job_get_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(jobs.a_jobs_response.name, jobs.a_jobs_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(jobs.list_jobs_response.name, jobs.list_jobs_response)


@namespace.route('/')
class JobCreateGetPost(Resource):
    @namespace.doc('jobs/create')
    @namespace.expect(jobs.jobs_model)
    # @namespace.marshal_with(jobs.a_jobs_response)
    @namespace.response(200, 'Created job', jobs.a_jobs_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        body = request.json
        body['author'] = get_jwt_identity()
        result = JobService.insert(body)
        Tasks = TaskService.createTasks(body, result)
        res = result.to_json()
        res['tasks'] = Tasks
        return {'success': True, 'data': res}, 200

    @namespace.doc('job/get')
    # @namespace.marshal_with(jobs.list_jobs_response)
    @namespace.response(200, 'list jobs current user', jobs.list_jobs_response)
    @namespace.response(404, 'jobs not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        result = JobService.select_jobs(author)
        for job in result['omeroIds']:
            for omeroId in job['omeroIds']:
                print(omeroId)
        # TaskService.select_tasks('')

        if result is None:
            abort(404, 'jobs not found')

        return {'success': True, 'data': result}, 200
