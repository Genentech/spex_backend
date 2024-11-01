from fileinput import filename

import spex_common.services.Job as JobService
import spex_common.services.Task as TaskService
import spex_common.services.Script as ScriptService
import spex_common.services.Pipeline as PipelineService
import spex_common.services.Utils as Utils
from spex_common.models.Status import TaskStatus
from flask_restx import Namespace, Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import jobs, responses
import os
import tempfile
from flask import send_file
import zipfile
from routes.api.v1.tasks import create_zarr_archive, ZarrStatus

namespace = Namespace('Jobs', description='Jobs CRUD operations')

namespace.add_model(jobs.jobs_model.name, jobs.jobs_model)
namespace.add_model(jobs.job_get_model.name, jobs.job_get_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(jobs.a_jobs_response.name, jobs.a_jobs_response)
namespace.add_model(jobs.jobs_update_model.name, jobs.jobs_update_model)
namespace.add_model(jobs.jobs_status_update_model.name, jobs.jobs_status_update_model)
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
        body.update(status=TaskStatus.pending_approval.value)

        if body.get('params') is None:
            body['params'] = {}

        result = JobService.insert(body, history=body)
        tasks = TaskService.create_tasks(body, result)
        result = result.to_json()
        result['tasks'] = tasks
        return {'success': True, 'data': result}, 200

    @namespace.doc('job/get', security='Bearer')
    @namespace.marshal_with(jobs.list_jobs_response)
    @namespace.response(200, 'list jobs current user', jobs.list_jobs_response)
    @namespace.response(404, 'jobs not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):

        result = JobService.select_jobs(**{'author': get_jwt_identity()})
        if not result:
            return {'success': False, 'message': 'jobs not found', 'data': {}}, 200

        for job in result:
            job['tasks'] = TaskService.select_tasks_edge(job.get('_id'))
            if job.get('status') is None or job.get('status') == '':
                job.update(status=TaskStatus.pending_approval.value)

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
        if not result:
            return {'success': False, 'message': 'job not found', 'data': {}}, 200

        job = result[0]
        job['tasks'] = TaskService.select_tasks_edge(job.get('_id'))
        if job.get('status') is None or job.get('status') == '':
            job.update(status=TaskStatus.pending_approval.value)

        return {'success': True, 'data': job}, 200

    @namespace.doc('job/put', security='Bearer')
    @namespace.marshal_with(jobs.a_jobs_response)
    @namespace.expect(jobs.jobs_update_model)
    @namespace.response(404, 'job not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def put(self, _id):

        result = JobService.select_jobs(**{'author': get_jwt_identity(), '_key': _id})
        if not result:
            return {'success': False, 'message': 'job not found', 'data': {}}, 200
        body = request.json
        body['author'] = get_jwt_identity()

        updated_job = JobService.update_job(id=_id, data=body, history=body)
        return {'success': True, 'data': updated_job}, 200

    @namespace.doc('job/delete', security='Bearer')
    @namespace.marshal_with(jobs.a_jobs_response)
    @namespace.response(404, 'job not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def delete(self, _id):

        result = JobService.select_jobs(**{'author': get_jwt_identity(), '_key': _id})
        if not result:
            return {'success': False, 'message': 'job not found', 'data': {}}, 200

        tasks = TaskService.select_tasks_edge(_id)
        for task in tasks:
            JobService.delete_connection(_from=_id, _to=task['_id'])
            TaskService.delete(task['id'])

        deleted = JobService.delete(_id).to_json()
        deleted['tasks'] = tasks
        if deleted.get('status') is None or deleted.get('status') == '':
            deleted.update(status=TaskStatus.pending_approval.value)

        return {'success': True, 'data': deleted}, 200


@namespace.route('/type')
class Type(Resource):
    @namespace.doc('job/get_types', security='Bearer')
    @namespace.marshal_with(jobs.a_jobs_type_response)
    @namespace.response(404, 'job type not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):
        data = ScriptService.scripts_list()
        return {'success': True, 'data': data}, 200


@namespace.route('/type/<string:script_type>')
@namespace.param('script_type', 'script type')
class Type(Resource):
    @namespace.doc('job/get_script_info', security='Bearer')
    # @namespace.marshal_with(jobs.a_jobs_response)
    @namespace.response(404, 'script type not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self, script_type):
        if script_type not in ScriptService.scripts_list():
            return {'success': False, 'message': 'Cannot find this type of job'}, 404

        data = ScriptService.get_script_structure(script_type)

        return {'success': True, 'data': data}, 200


@namespace.param('status', 'status')
@namespace.param('name', 'name')
@namespace.route('/find/')
class JobFind(Resource):
    @namespace.doc('job/find_all', security='Bearer')
    @namespace.marshal_with(jobs.list_jobs_response)
    @namespace.response(200, 'list jobs current user', jobs.list_jobs_response)
    @namespace.response(404, 'jobs not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):

        condition = {
            'author': get_jwt_identity(),
        }
        if pipeline_id := request.args.get('pipeline_id', None):
            pipelines = PipelineService.get_tree(pipeline_id=pipeline_id)
            jobs_list = PipelineService.get_jobs(pipelines, prefix=True)
            condition['_id'] = jobs_list
        for arg in request.args:
            if arg == 'pipeline_id':
                continue
            value = request.args.getlist(arg)
            if arg == 'status':
                condition[arg] = [int(item) for item in value]
            else:
                condition[arg] = value

        result = JobService.select_jobs(**condition)

        if not result:
            return {'success': False, 'message': 'jobs not found', 'data': {}}, 200

        for job in result:
            job['tasks'] = TaskService.select_tasks_edge(job.get('_id'))
            if job.get('status') is None or job.get('status') == '':
                job.update(status=TaskStatus.pending_approval.value)

        return {'success': True, 'data': result}, 200

    @namespace.doc('job/edit_all', security='Bearer')
    @namespace.expect(jobs.jobs_status_update_model)
    @namespace.response(200, 'list updated jobs current user', jobs.list_jobs_response)
    @namespace.response(404, 'jobs not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def put(self):

        condition = {
            'author': get_jwt_identity(),
        }
        if pipeline_id := request.args.get('pipeline_id', None):
            pipelines = PipelineService.get_tree(pipeline_id=pipeline_id)
            jobs_list = PipelineService.get_jobs(pipelines, prefix=True)
            condition['_id'] = jobs_list
        for arg in request.args:
            if arg == 'pipeline_id':
                continue
            value = request.args.getlist(arg)
            if arg == 'status':
                condition[arg] = [int(item) for item in value]
            else:
                condition[arg] = value

        result = JobService.select_jobs(**condition)

        if not result:
            return {'success': False, 'message': 'jobs not found', 'data': {}}, 200

        statuses = [status.value for status in TaskStatus]
        to_update = request.json["status"]
        if to_update not in statuses:
            return {'success': False, 'message': f'status can be in {statuses}', 'data': {}}, 200

        for job in result:
            updated_job = JobService.update_job(id=job.get("id"), data={"status": to_update})
            if updated_job.get('status') == to_update:
                job['status'] = to_update
                job['tasks'] = TaskService.select_tasks_edge(job.get('_id'))
                if job.get('status') is None or job.get('status') == '':
                    for task in job['tasks']:
                        task['status'] = to_update

        return {'success': True, 'data': result}, 200


def list_files(startpath):
    tree = {}
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        if level == 0:
            subtree = tree
        else:
            parent_dirs = root.replace(startpath, '').split(os.sep)[1:]
            subtree = tree
            for parent_dir in parent_dirs:
                subtree = subtree.setdefault(parent_dir, {})

        for _dir in dirs:
            subtree.setdefault(_dir, {})

        for file in files:
            subtree[file] = None

    return tree


@namespace.route('/merged_result/<string:job_id>')
@namespace.param('job_id', 'Job id')
class MergedResult(Resource):
    @namespace.doc('job/get_merged_result', security='Bearer')
    @namespace.response(404, 'Job or Tasks not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self, job_id):

        tasks = TaskService.select_tasks_edge(f'jobs/{job_id}')
        if not tasks:
            return {'success': False, 'message': 'Tasks not found', 'data': {}}, 404

        show_structure = request.args.get('show_structure', None)
        path_list: list = []
        for task in tasks:
            if path := Utils.getAbsoluteRelative(task.get('result')):
                if create_zarr_archive(task) == ZarrStatus.complete:
                    path_list.append(f'{os.path.dirname(path)}/static/cells.h5ad.zarr')
        if path_list and not show_structure:
            temp_dir = tempfile.mkdtemp()
            zip_file_path = os.path.join(temp_dir, "merged_result.zip")

            with zipfile.ZipFile(zip_file_path, "w") as zipf:
                for path in path_list:
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            absolute_path = os.path.join(root, file)
                            relative_path = os.path.relpath(absolute_path, path)
                            archive_path = os.path.join(os.path.basename(path), relative_path)
                            zipf.write(absolute_path, archive_path)

            return send_file(
                zip_file_path,
                attachment_filename="merged_result.zip",
                as_attachment=True,
                mimetype="application/zip",
            )
        if path_list and show_structure.lower() == 'true':
            folder_trees = {os.path.basename(path): list_files(path) for path in path_list}
            return {'success': True, 'data': folder_trees}, 200


@namespace.route('/anndata_result/<string:job_id>')
@namespace.param('job_id', 'Job id')
class MergedResult(Resource):
    @namespace.doc('job/anndata_result', security='Bearer')
    @namespace.response(404, 'Job or Tasks not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self, job_id):

        tasks = TaskService.select_tasks_edge(f'jobs/{job_id}')
        if not tasks:
            return {'success': False, 'message': 'Tasks not found', 'data': {}}, 200

        path_list: list = []
        for task in tasks:

            if task.get("result") is None:
                return {"success": False, "message": "result not found", "data": {}}, 200

            path = task.get("result")
            path = Utils.getAbsoluteRelative(path, absolute=True)
            filename, ext = os.path.splitext(path)
            filename = filename + '.h5ad'
            if os.path.exists(filename):
                path_list.append(filename)

        if path_list:
            temp_dir = tempfile.mkdtemp()
            zip_file_path = os.path.join(temp_dir, "anndata_result.zip")

            with zipfile.ZipFile(zip_file_path, "w") as zipf:
                for index, path in enumerate(path_list, start=1):
                    new_filename = f"{index}_{os.path.basename(path)}"
                    zipf.write(path, new_filename)

            return send_file(
                zip_file_path,
                attachment_filename="anndata_result.zip",
                as_attachment=True,
                mimetype="application/zip",
            )

