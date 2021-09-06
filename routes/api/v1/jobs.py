import services.Job as JobService
import services.Task as TaskService
import services.Script_worker as ScriptService
import os
from glob import glob
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
namespace.add_model(jobs.a_jobs_type_response.name, jobs.a_jobs_type_response)


@namespace.route('')
class JobCreateGetPost(Resource):
    @namespace.doc('jobs/create', security='Bearer')
    @namespace.expect(jobs.jobs_model)
    # @namespace.marshal_with(jobs.a_jobs_response)
    @namespace.response(200, 'Created job', jobs.a_jobs_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        body = request.json
        body['author'] = get_jwt_identity()
        if body.get('status') is None or body.get('status') == '':
            body.update(status=0)
        result = JobService.insert(body)
        tasks = TaskService.create_tasks(body, result)
        res = result.to_json()
        res['tasks'] = tasks
        return {'success': True, 'data': res}, 200

    @namespace.doc('job/get', security='Bearer')
    @namespace.marshal_with(jobs.list_jobs_response)
    @namespace.response(200, 'list jobs current user', jobs.list_jobs_response)
    @namespace.response(404, 'jobs not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):

        result = JobService.select_jobs(**{'author': get_jwt_identity()})
        if result is None:
            return {'success': False, 'message': 'jobs not found', 'data': {}}, 200
        for job in result:
            job['tasks'] = TaskService.select_tasks_edge(job.get('_id'))
            if job.get('status') is None or job.get('status') == '':
                job.update(status=0)

        return {'success': True, 'data': result}, 200


@namespace.route('/<string:_id>')
class Item(Resource):
    @namespace.doc('job/get', security='Bearer')
    @namespace.marshal_with(jobs.a_jobs_response)
    @namespace.response(404, 'job not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self, _id):

        result = JobService.select_jobs(**{'author': get_jwt_identity(), '_key': _id})
        if result is None or result == []:
            return {'success': False, 'message': 'job not found', 'data': {}}, 200
        for job in result:
            job['tasks'] = TaskService.select_tasks_edge(job.get('_id'))
            if job.get('status') is None or job.get('status') == '':
                job.update(status=0)
        return {'success': True, 'data': result[0]}, 200

    @namespace.doc('job/put', security='Bearer')
    @namespace.marshal_with(jobs.a_jobs_response)
    @namespace.expect(jobs.jobs_update_model)
    @namespace.response(404, 'job not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def put(self, _id):

        result = JobService.select_jobs(**{'author': get_jwt_identity(), '_key': _id})
        if result is None or result == []:
            return {'success': False, 'message': 'job not found', 'data': {}}, 200
        for job in result:
            job = JobService.update(id=_id, data=request.json).to_json()
            tasks = TaskService.select_tasks_edge(job['_id'])
            updated_tasks = []
            for task in tasks:
                task = TaskService.update(_id=task['id'], data=request.json)
                updated_tasks.append(task.to_json())
            job['tasks'] = updated_tasks
            if job.get('status') is None or job.get('status') == '':
                job.update(status=0)

            return {'success': True, 'data': job}, 200

    @namespace.doc('job/delete', security='Bearer')
    @namespace.marshal_with(jobs.a_jobs_response)
    @namespace.response(404, 'job not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def delete(self, _id):

        result = JobService.select_jobs(**{'author': get_jwt_identity(), '_key': _id})
        if result is None or result == []:
            return {'success': False, 'message': 'job not found', 'data': {}}, 200
        for job in result:
            tasks = TaskService.select_tasks_edge(job['_id'])
            for task in tasks:
                JobService.delete_connection(_from=job['_id'], _to=task['_id'])
                TaskService.delete(task['id'])

            deleted = JobService.delete(_id).to_json()
            deleted['tasks'] = tasks
            if deleted.get('status') is None or deleted.get('status') == '':
                deleted.update(status=0)

            return {'success': True, 'data': deleted}, 200


@namespace.route('/type/<string:job_type>')
class Type(Resource):
    @namespace.doc('job/get_job_info', security='Bearer')
    # @namespace.marshal_with(jobs.a_jobs_response)
    @namespace.response(404, 'job type not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    # @jwt_required()
    def get(self, job_type):
        if job_type not in ScriptService.scripts_list():
            return {'success': False, 'message': 'Cannot find this type of job'}, 200

        data = ScriptService.get_script_structure(job_type)

        return {'success': True, 'data': data}, 200


@namespace.route('/type')
class Type(Resource):
    @namespace.doc('job/get_types', security='Bearer')
    @namespace.marshal_with(jobs.a_jobs_type_response)
    @namespace.response(404, 'job type not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):

        return {'success': True, 'data': ScriptService.scripts_list()}, 200
