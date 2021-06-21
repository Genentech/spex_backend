import services.Job as JobService
import services.Task as TaskService
from flask_restx import Namespace, Resource
from flask import request
# from models.Job import Job
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import jobs, responses


namespace = Namespace('Jobs', description='Jobs CRUD operations')

namespace.add_model(jobs.jobs_model.name, jobs.jobs_model)
namespace.add_model(jobs.job_get_model.name, jobs.job_get_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(jobs.a_jobs_response.name, jobs.a_jobs_response)
namespace.add_model(jobs.jobs_update_model.name, jobs.jobs_update_model)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(jobs.list_jobs_response.name, jobs.list_jobs_response)


@namespace.route('')
class JobCreateGetPost(Resource):
    @namespace.doc('jobs/create', security='Bearer')
    @namespace.expect(jobs.jobs_model)
    @namespace.marshal_with(jobs.a_jobs_response)
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

    @namespace.doc('job/get', security='Bearer')
    @namespace.marshal_with(jobs.list_jobs_response)
    @namespace.response(200, 'list jobs current user', jobs.list_jobs_response)
    @namespace.response(404, 'jobs not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):

        result = JobService.select_jobs(**{'author': get_jwt_identity()})
        for job in result:
            job['tasks'] = TaskService.select_tasks_edge(job.get('_id'))

        if result is None:
            return {'success': False, 'message': 'jobs not found', 'data': {}}, 200

        return {'success': True, 'data': result}, 200


@namespace.route('/<string:id>')
class Item(Resource):
    @namespace.doc('job/get', security='Bearer')
    @namespace.marshal_with(jobs.a_jobs_response)
    @namespace.response(404, 'job not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self, id):

        result = JobService.select_jobs(**{'author': get_jwt_identity(), '_key': id})
        if result is None or result == []:
            return {'success': False, 'message': 'job not found', 'data': {}}, 200
        for job in result:
            job['tasks'] = TaskService.select_tasks_edge(job.get('_id'))
        return {'success': True, 'data': result[0]}, 200

    @namespace.doc('job/put', security='Bearer')
    @namespace.marshal_with(jobs.a_jobs_response)
    @namespace.expect(jobs.jobs_update_model)
    @namespace.response(404, 'job not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def put(self, id):

        result = JobService.select_jobs(**{'author': get_jwt_identity(), '_key': id})
        if result is None or result == []:
            return {'success': False, 'message': 'job not found', 'data': {}}, 200
        for job in result:
            job = JobService.update(id=id, data=request.json).to_json()
            tasks = TaskService.select_tasks_edge(job['_id'])
            updated_tasks = []
            for task in tasks:
                task = TaskService.update(id=task['id'], data=request.json)
                updated_tasks.append(task.to_json())
            job['tasks'] = updated_tasks

        return {'success': True, 'data': job}, 200

    @namespace.doc('job/delete', security='Bearer')
    @namespace.marshal_with(jobs.a_jobs_response)
    @namespace.response(404, 'job not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def delete(self, id):

        result = JobService.select_jobs(**{'author': get_jwt_identity(), '_key': id})
        if result is None or result == []:
            return {'success': False, 'message': 'job not found', 'data': {}}, 200
        for job in result:
            tasks = TaskService.select_tasks_edge(job['_id'])
            for task in tasks:
                JobService.delete_connection(_from=job['_id'], _to=task['_id'])
                TaskService.delete(task['id'])

            deleted = JobService.delete(id).to_json()
            deleted['tasks'] = tasks

        return {'success': True, 'data': deleted}, 200
