import services.Pipeline as PipelineService
import services.Task as TaskService
import services.Job as JobService
import services.Project as ProjectService
from flask_restx import Namespace, Resource
from flask import request
# from models.Job import Job
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import pipeline, responses
from spex_common.modules.database import db_instance

namespace = Namespace('Pipeline', description='Pipeline CRUD operations')

namespace.add_model(pipeline.pipeline_model.name, pipeline.pipeline_model)
namespace.add_model(pipeline.pipeline_post_model.name, pipeline.pipeline_post_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(pipeline.a_pipeline_response.name, pipeline.a_pipeline_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(pipeline.list_pipeline_response.name, pipeline.list_pipeline_response)
namespace.add_model(pipeline.pipeline_get_model.name, pipeline.pipeline_get_model)
namespace.add_model(pipeline.task_resource_image_connect_to_job.name, pipeline.task_resource_image_connect_to_job)


def recursion_query(itemid, _depth):

    text = 'FOR d IN jobs ' + \
          f'FILTER d._id == "{itemid}" ' + \
           'LET jobs = (' + \
          f'FOR b IN 1..1 OUTBOUND "{itemid}"' + ' GRAPH "pipeline" FILTER b._id LIKE "job/%"  RETURN {"name": b.name, "id": b._key, "status": b.complete } )' + \
           'LET resources = (' + \
          f'FOR b IN 1..1 INBOUND "{itemid}"' + ' GRAPH "pipeline" FILTER b._id LIKE "resource/%"  RETURN {"name": b.name, "id": b._key, "status": 0 } )' + \
           ' RETURN MERGE({"id": d._key, "name": d.name, "status": d.complete}, {"jobs": jobs, "tasks": tasks, "resources": resources})'

    result = db_instance().query(text)
    if len(result) > 0:
        tree = result[0]
        tree['tasks'] = TaskService.select_tasks_edge(itemid)
    else:
        return

    i = 0
    if _depth < 50:
        if result[0]['jobs'] is not None and len(result[0]['jobs']) > 0:
            while i < len(result[0]['jobs']):
                _id = 'job/' + str(result[0]['jobs'][i]['id'])
                tree['jobs'][i] = recursion_query(_id, _depth + 1)
                i += 1
    return tree


def depth(x):
    if type(x) is dict and x:
        return 1 + max(depth(x[a]) for a in x)
    if type(x) is list and x:
        return 1 + max(depth(a) for a in x)
    return 0


def get_jobs(x):
    jobs = []
    if type(x) is list and x:
        for job in x:
            if job is None:
                return jobs
            jobs.append(job.get('id'))
            if job.get('jobs') is not None:
                jobs = jobs + get_jobs(job.get('jobs'))
    return jobs


def search_in_arr_dict(key, value, arr):
    founded = []
    for item in arr:
        item_value = item.get(key)
        if value is not None and item_value == value:
            founded.append(arr.index(item))
    return founded


# directions between pipelines jobs tasks
@namespace.route('/<string:project_id>/<string:parent_id>')
@namespace.param('project_id', 'project id')
@namespace.param('parent_id', 'who is daddy')
class PipelineCreatePost(Resource):
    @namespace.doc('pipeline_directions/insert', security='Bearer')
    @namespace.expect(pipeline.task_resource_image_connect_to_job)
    # @namespace.marshal_with(projects.a_project_response)
    @namespace.response(200, 'Created connection', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self, project_id, parent_id):
        body = request.json
        author = get_jwt_identity()
        t_id_arr = body.get('tasks_ids')
        r_id_arr = body.get('resource_ids')
        j_id_arr = body.get('job_ids')
        project = ProjectService.select(project_id)
        if t_id_arr is not None:
            not_founded_in_project = list(set(t_id_arr) - set(project.taskIds))
            if len(not_founded_in_project) > 0:
                message = f'tasks with ids: {not_founded_in_project} not found in project data'
                return {'success': False, "message": message}, 200

        if r_id_arr is not None:
            not_founded_in_project = list(set(r_id_arr) - set(project.resource_ids))
            if len(not_founded_in_project) > 0:
                message = f'resource with ids: {not_founded_in_project} not found in project data'
                return {'success': False, "message": message}, 200

        parent = PipelineService.select_pipeline(collection='pipeline', _key=parent_id, author=author, project=project_id, one=True)
        if parent is None:
            parent = PipelineService.select_pipeline(collection='jobs', _key=parent_id, author=author, one=True)
            if parent is None:
                message = f'job or pipeline with id: {parent_id} not found'
                return {'success': False, "message": message}, 200
        founded_t = []
        if t_id_arr is not None:
            founded_t = TaskService.select_tasks(condition='in', _key=t_id_arr)
            if founded_t is None:
                founded_t = []
                message = f'tasks not found {t_id_arr}'
                return {'success': False, "message": message}, 200
        founded_r = []
        if r_id_arr is not None:
            founded_r = JobService.select_jobs(condition='in', _key=r_id_arr, collection='resource')
            if founded_r is None:
                founded_r = []
                message = f'resources not found {r_id_arr}'
                return {'success': False, "message": message}, 200
        founded_j = []
        if j_id_arr is not None:
            founded_j = PipelineService.select_pipeline(collection='jobs', _key=j_id_arr, condition='in', author=[author])
            if founded_j is None:
                message = f'jobs not found {j_id_arr}'
                founded_j = []
                return {'success': False, "message": message}, 200

        founded_c = list(founded_t + founded_r + founded_j)
        arr_founded_id = []
        existed = []
        for item in founded_c:
            c_id = item.get('id')
            f_t = {}
            f_t.update({'_from': str(item.get('_id'))})
            f_t.update({'_to': 'job/'+str(parent_id)})
            f_t.update({'author': author})
            f_t.update({'project': project_id})
            has = PipelineService.select_pipeline(_from=str(str(item.get('_id'))), _to='job/'+str(parent_id), author=author, project=project_id)
            if has is None:
                PipelineService.insert(f_t)
                arr_founded_id.append(c_id)
            else:
                existed.append(c_id)

        not_founded_c = list(set(t_id_arr if t_id_arr is not None else []) - set(arr_founded_id if arr_founded_id is not None else []) - set(existed if existed is not None else []))
        result = {'Added': arr_founded_id, 'NotFounded': not_founded_c, 'Existed': existed}

        return {'success': True, 'data': result}, 200
# directions between pipelines jobs tasks


# get pipelines list with child's
@namespace.route('/<string:project_id>')
@namespace.param('project_id', 'project id')
class PipelineGet(Resource):
    @namespace.doc('pipelines/get', security='Bearer', description="get all project pipelines with children ")
    # @namespace.expect(projects.projects_model)
    # @namespace.marshal_with(projects.a_project_response)
    @namespace.response(200, 'Get pipeline and children', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self, project_id):

        author = get_jwt_identity()
        if ProjectService.select_projects(_key=project_id, author=author) is None:
            return {'success': False, 'message': f'project with id: {project_id} not found'}, 200

        pipelines = PipelineService.select_pipeline(collection='pipeline', author=author, project=project_id)

        lines = []
        if pipelines is None:
            return {'success': True, 'data': {"pipelines": lines}}, 200
        for pipeline_ in pipelines:
            res = []
            jobs = PipelineService.select_pipeline(author=author, _from=pipeline_.get('_id'))
            if jobs is None:
                pipeline_.pop('_from', None)
                pipeline_.pop('_to', None)
                pipeline_.update({'jobs': res})
                lines.append(pipeline_)
                continue
            for job in jobs:
                res.append(recursion_query(job['_to'], 0))
            pipeline_.pop('_from', None)
            pipeline_.pop('_to', None)
            pipeline_.update({'jobs': res})
            lines.append(pipeline_)

        result = {"pipelines": lines}

        return {'success': True, 'data': result}, 200


# get pipeline with children's
@namespace.route('/path/<string:project_id>/<string:pipeline_id>')
@namespace.param('project_id', 'project id')
@namespace.param('pipeline_id', 'pipeline_id')
class PipelineGetList(Resource):
    @namespace.doc('pipelines/get', security='Bearer', description='get full content for one pipeline')
    # @namespace.expect(projects.projects_model)
    # @namespace.marshal_with(projects.a_project_response)
    @namespace.response(200, 'Get pipeline and child as list', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self, project_id, pipeline_id):
        author = get_jwt_identity()
        if ProjectService.select_projects(_key=project_id, author=author) is None:
            return {'success': False, 'message': f'project with id: {project_id} not found'}, 200

        _pipelines = PipelineService.select_pipeline(collection='pipeline', author=author, project=project_id, _key=pipeline_id)

        lines = []
        if _pipelines is None:
            return {'success': True, 'data': {"pipelines": lines}}, 200
        for _pipeline in _pipelines:
            res = []
            jobs = PipelineService.select_pipeline(author=author, _from=_pipeline.get('_id'))
            if jobs is None:
                _pipeline.pop('_from', None)
                _pipeline.pop('_to', None)
                _pipeline.update({'jobs': res})
                lines.append(_pipeline)
                continue
            for job in jobs:
                res.append(recursion_query(job['_to'], 0))
            _pipeline.pop('_from', None)
            _pipeline.pop('_to', None)
            _pipeline.update({'jobs': res})
            lines.append(_pipeline)

        result = {"pipelines": lines}

        return {'success': True, 'data': result}, 200


# insert new job to another job, or to pipeline
@namespace.route('/job/<string:project_id>/<string:parent_id>')
@namespace.param('project_id', 'project id')
@namespace.param('parent_id', 'who is daddy pipeline or another job')
class JobCreate(Resource):
    @namespace.doc('job/insert', security='Bearer')
    @namespace.expect(pipeline.pipeline_model)
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(200, 'Created job', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self, project_id, parent_id):
        body = request.json
        author = get_jwt_identity()

        if ProjectService.select_projects(_key=project_id, author=author) is None:
            return {'success': False, 'message': f'project with id: {project_id} not found'}, 200

        parent = PipelineService.select_pipeline(collection='pipeline', _key=parent_id, author=author, project=project_id, one=True)
        if parent is None:
            parent = PipelineService.select(id=parent_id, collection='jobs', to_json=True, one=True)
            if parent is None:
                return {'success': False, 'message': f'job or pipeline with id: {parent_id} not found'}, 200

        data = {'name': body.get('name')}
        data.update({'author': author})
        data.update({'complete': 0})
        data.update({'project': project_id})
        data.update({'parent': parent_id})
        job = PipelineService.insert(data, collection='jobs')
        if job is not None:
            job = job.to_json()
        f_t = {}
        f_t.update({'_from': parent.get('_id')})
        f_t.update({'_to': job.get('_id')})
        f_t.update({'author': author})
        f_t.update({'project': project_id})
        f_t.update({'parent': parent_id})
        _pipeline = PipelineService.insert(f_t)
        job.update({'nested': _pipeline.to_json()})

        return {'success': True, 'data': job}, 200
# insert new job to another job, or to pipeline


# insert pipeline to project
@namespace.route('/create/<string:project_id>')
@namespace.param('project_id', 'project id')
class PipelineCreate(Resource):
    @namespace.doc('pipeline/insert', security='Bearer', description='First step create a pipeline')
    @namespace.expect(pipeline.pipeline_model)
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(200, 'Created pipeline', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self, project_id):
        body = request.json
        author = get_jwt_identity()
        name = body.get('name')

        data = {'name': name}
        data.update({'author': author})
        if ProjectService.select_projects(_key=project_id, author=author) is None:
            return {'success': False, 'message': f'project with id: {project_id} not found'}, 200

        data.update({'complete': 0})
        data.update({'project': project_id})
        _pipeline = PipelineService.insert(data, collection='pipeline').to_json()
        f_t = {}
        f_t.update({'_from': 'projects/'+project_id})
        f_t.update({'_to': _pipeline.get('_id')})
        f_t.update({'author': author})
        f_t.update({'project': project_id})
        pipeline_direction = PipelineService.insert(f_t)
        _pipeline.update({'nested': pipeline_direction.to_json()})
        return {'success': True, 'data': _pipeline}, 200
# insert pipeline to project


# update pipeline data
@namespace.route('/update/<string:project_id>/<string:pipeline_job_id>')
@namespace.param('project_id', 'project id')
@namespace.param('pipeline_job_id', 'pipeline or job id')
class PipelineJobUpdate(Resource):
    @namespace.doc('pipeline/update', security='Bearer')
    @namespace.expect(pipeline.pipeline_model)
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(200, 'Update pipeline', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def put(self, project_id, pipeline_job_id):
        author = get_jwt_identity()
        body = request.json
        if ProjectService.select_projects(_key=project_id, author=author) is None:
            return {'success': False, 'message': 'project not found'}, 200

        if PipelineService.select_pipeline(collection='pipeline', _key=pipeline_job_id, author=author, project=project_id) is not None:
            pipeline_ = PipelineService.update(collection='pipeline', id=pipeline_job_id, data=body)
        else:
            if PipelineService.select_pipeline(collection='jobs', _key=pipeline_job_id, author=author, project=project_id) is None:
                return {'success': False, 'message': 'pipeline or job not found'}, 200
            else:
                pipeline_ = PipelineService.update(collection='jobs', id=pipeline_job_id, data=body)

        return {'success': True, 'data': pipeline_.to_json()}, 200
# update pipeline data


@namespace.route('/delete/<string:project_id>/<string:pipeline_job_id>')
@namespace.param('project_id', 'project id')
@namespace.param('pipeline_job_id', 'pipeline or job id')
class PipelineDelete(Resource):
    @namespace.doc('pipeline_jobs/delete', security='Bearer')
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(404, 'Object not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def delete(self, project_id, pipeline_job_id):
        author = get_jwt_identity()
        project = ProjectService.select_projects(_key=project_id, author=author)   # only author projects show
        if project is None:
            return {'success': False, 'message': 'project not found'}, 200
        pipeline_ = PipelineService.select_pipeline(collection='pipeline', _key=pipeline_job_id, author=author, project=project_id, one=True)
        if pipeline_ is None:
            pipeline_ = PipelineService.select_pipeline(collection='jobs', _key=pipeline_job_id, author=author, one=True)
            if pipeline_ is None:
                return {'success': False, 'message': 'pipeline not found'}, 200

        jobs = PipelineService.select_pipeline(author=author, _from=pipeline_.get('_id'))
        res = []
        if jobs is not None:
            for job in jobs:
                res.append(recursion_query(job['_to'], 0))

        pipeline_.update({'jobs': res})
        children_to_delete = get_jobs(pipeline_.get('jobs'))
        for child in reversed(children_to_delete):
            PipelineService.delete(_from=child)
            PipelineService.delete(_to=child)
            PipelineService.delete(collection='jobs', _key=child)
        PipelineService.delete(collection=pipeline_.get('_id').replace('/'+pipeline_.get('id'), ''), _key=pipeline_.get('id'))
        PipelineService.delete(_to=pipeline_.get('_id'))
        return {'success': True, 'data': pipeline_}, 200


@namespace.route('/conn/<string:parent_id>/<string:child_id>/<string:project_id>')
@namespace.param('parent_id', 'parent id(job or pipeline)')
@namespace.param('child_id', 'child id only job')
@namespace.param('project_id', 'project id')
class PipelineDelete(Resource):
    @namespace.doc('pipeline_jobs_reconnect_job/reconnect', security='Bearer', description='Second step connect between pipeline and created job or existed')
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(404, 'Object not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self, parent_id, child_id, project_id):
        author = get_jwt_identity()
        if child_id == parent_id:
            return {'success': False, 'message': 'child and parent id can not be same'}
        project = ProjectService.select_projects(_key=project_id, author=author)   # only author projects show
        if project is None:
            return {'success': False, 'message': 'project not found'}, 200
        _parent = PipelineService.select_pipeline(collection='pipeline', _key=parent_id, author=author, project=project_id, one=True)
        if _parent is None:
            _parent = PipelineService.select_pipeline(collection='jobs', _key=parent_id, author=author, one=True)
            if _parent is None:
                return {'success': False, 'message': 'parent not found'}, 200

        _child = PipelineService.select_pipeline(collection='jobs', _key=child_id, author=author, one=True)
        if _child is None:
            return {'success': False, 'message': 'child not found'}, 200
        if lines := PipelineService.select_pipeline(collection='pipeline_direction', _to=_child['_id'], author=author, project=project_id, one=False):
            PipelineService.delete(collection='pipeline_direction', _to=_child['_id'], author=author, project=project_id)

        ft = {'_from': str(_parent['_id']),
              '_to': str(_child['_id']),
              'author': author,
              'project': str(project_id)}
        data = PipelineService.insert(data=ft, collection='pipeline_direction')
        return {'success': True, 'data': data}, 200
