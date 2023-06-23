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
import anndata
import pandas as pd
import numpy as np
import os
import tempfile
from flask import send_file
from scipy.stats import zscore
import pickle
import zipfile
import io


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


@namespace.route('/merged_result/<string:job_id>')
@namespace.param('job_id', 'Job id')
class MergedResult(Resource):
    @namespace.doc('job/get_merged_result', security='Bearer')
    @namespace.response(404, 'Job or Tasks not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self, job_id):

        csv_data = {}

        def save_to_csv(adata):
            expression_data = pd.DataFrame(adata.X, columns=adata.var.index, index=adata.obs.index)
            metadata = adata.obs

            expression_data_buffer = io.StringIO()
            metadata_buffer = io.StringIO()

            expression_data.to_csv(expression_data_buffer)
            metadata.to_csv(metadata_buffer)

            return expression_data_buffer.getvalue(), metadata_buffer.getvalue()

        def create_anndata(data):
            df = data['dataframe']
            df.index = df.index.astype(str)

            coordinates = np.column_stack((df['centroid-1'], df['centroid-0']))
            celltype = df[['label']].copy()
            celltype = celltype.rename(columns={'label': 'Cell_ID'})
            celltype['Cell_ID'] = celltype['Cell_ID'].astype('category')
            cl = data["channel_list"]
            if not cl:
                cl = data["all_channels"]
            expression_data = np.array(df[cl[0].lower().replace('target:', '')])
            expression_data = expression_data.reshape(-1, 1)
            expression_data = np.apply_along_axis(zscore, axis=0, arr=expression_data)

            adata = anndata.AnnData(
                X=expression_data.astype(np.float32),
                obs=pd.DataFrame(index=df.index),
                obsm={'spatial': coordinates},
                layers={'zscored': expression_data.astype(np.float32)},
            )

            for col in df.columns:
                adata.obs[col] = df[col]

            adata.obs['Cell_ID'] = celltype['Cell_ID']

            return adata

        def merge_tasks_result(_tasks):
            merged_adata = None
            for task in _tasks:
                task_result_path = task.get("result")
                task_result_path = Utils.getAbsoluteRelative(task_result_path, absolute=True)
                if task_result_path is None or not os.path.exists(task_result_path):
                    continue

                with open(task_result_path, "rb") as infile:
                    data = pickle.load(infile)
                    adata = create_anndata(data)
                    expression_data_csv, metadata_csv = save_to_csv(adata)
                    csv_data[task["id"]] = {"expression_data": expression_data_csv, "metadata": metadata_csv}

                    adata.obs['batch'] = task["id"]

                    if merged_adata is None:
                        merged_adata = adata
                    else:
                        merged_adata = merged_adata.concatenate(adata, batch_key='batch')

            return merged_adata

        tasks = TaskService.select_tasks_edge(f'jobs/{job_id}')
        if not tasks:
            return {'success': False, 'message': 'Tasks not found', 'data': {}}, 404

        show_structure = request.args.get('show_structure', None)

        if m_data := merge_tasks_result(tasks):
            if show_structure:
                data_structure = {
                    "obs": m_data.obs.head(10).to_dict(),
                    "var": m_data.var.head(10).to_dict(),
                    "obsm": {k: v[:10].tolist() for k, v in m_data.obsm.items()},
                    "varm": {k: v[:10].tolist() for k, v in m_data.varm.items()},
                    "obsp": {k: v[:10].tolist() for k, v in m_data.obsp.items()},
                    "varp": {k: v[:10].tolist() for k, v in m_data.varp.items()},
                    "uns": list(m_data.uns.keys()),
                    "layers": {k: v[:10].tolist() for k, v in m_data.layers.items()},
                }

                return {'success': True, 'data': data_structure}, 200

            temp_dir = tempfile.mkdtemp()
            zip_file_path = os.path.join(temp_dir, "merged_result.zip")

            with zipfile.ZipFile(zip_file_path, "w") as zipf:
                for task_id, data in csv_data.items():
                    zipf.writestr(f"csv/{job_id}/{task_id}/expression_data.csv", data["expression_data"])
                    zipf.writestr(f"csv/{job_id}/{task_id}/metadata.csv", data["metadata"])

                with tempfile.NamedTemporaryFile(delete=False) as f:
                    m_data.write(f.name)
                    f.seek(0)
                    zipf.write(f.name, "merged_result.h5ad")

            return send_file(
                zip_file_path,
                attachment_filename="merged_result.zip",
                as_attachment=True,
                mimetype="application/zip",
            )
        else:
            return {'success': False, 'message': 'data not found', 'data': {}}, 404
