import spex_common.services.Pipeline as PipelineService
import spex_common.services.Project as ProjectService
import spex_common.services.Task as TaskService
import spex_common.services.Templates as TemplateService
import spex_common.services.Job as JobService
from spex_common.models.Status import TaskStatus
from flask_restx import Namespace, Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import pipeline, responses

namespace = Namespace('Pipeline', description='Pipeline CRUD operations')

namespace.add_model(pipeline.pipeline_model.name, pipeline.pipeline_model)
namespace.add_model(pipeline.pipeline_create_model.name, pipeline.pipeline_create_model)
namespace.add_model(pipeline.pipeline_post_model.name, pipeline.pipeline_post_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(pipeline.a_pipeline_response.name, pipeline.a_pipeline_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(pipeline.list_pipeline_response.name, pipeline.list_pipeline_response)
namespace.add_model(pipeline.pipeline_get_model.name, pipeline.pipeline_get_model)
namespace.add_model(pipeline.task_resource_image_connect_to_job.name, pipeline.task_resource_image_connect_to_job)
namespace.add_model(pipeline.pipeline_status_model.name, pipeline.pipeline_status_model)


# get pipelines list with child's
@namespace.route('s/<string:project_id>')
@namespace.param('project_id', 'project id')
class PipelineGet(Resource):
    @namespace.doc('pipelines/get', security='Bearer', description="get all project pipelines with children ")
    @namespace.response(200, 'Get pipeline and children', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.response(404, 'Not Found', responses.error_response)
    @jwt_required()
    def get(self, project_id):
        author = get_jwt_identity()

        if not ProjectService.select_projects(_key=project_id, author=author):
            return {'success': False, 'message': f'project with id: {project_id} not found'}, 404

        pipelines = PipelineService.select_pipeline(collection='pipeline', author=author, project=project_id)

        lines = []
        if not pipelines:
            return {'success': True, 'data': {"pipelines": lines}}, 200

        for item in pipelines:
            res = []
            jobs = PipelineService.select_pipeline(author=author, _from=item.get('_id'))

            if not jobs:
                item.pop('_from', None)
                item.pop('_to', None)
                item.update({'jobs': res})
                lines.append(item)
                continue

            for job in jobs:
                res.append(PipelineService.recursion_query(job['_to'], {}, 0, item.get('id')))

            item.pop('_from', None)
            item.pop('_to', None)
            item.update({'jobs': res})
            lines.append(item)

        result = {"pipelines": lines}

        return {'success': True, 'data': result}, 200

    @namespace.doc('pipeline/insert', security='Bearer', description='First step create a pipeline')
    @namespace.expect(pipeline.pipeline_create_model)
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(200, 'Created pipeline', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.response(404, 'Not Found', responses.error_response)
    @jwt_required()
    def post(self, project_id):
        body = request.json
        author = get_jwt_identity()
        name = body.get('name')

        if not ProjectService.select_projects(_key=project_id, author=author):
            return {'success': False, 'message': f'project with id: {project_id} not found'}, 404

        data = {
            'name': name,
            'author': author,
            'complete': 0,
            'project': project_id,
        }

        item = PipelineService.insert(data, collection='pipeline').to_json()

        link = {
            '_from': f'projects/{project_id}',
            '_to': item.get('_id'),
            'author': author,
            'project': project_id,
            'pipeline': item.get('id')
        }

        pipeline_direction = PipelineService.insert(link)

        item.update({'nested': pipeline_direction.to_json()})

        return {'success': True, 'data': item}, 200


@namespace.route('/<string:pipeline_id>')
@namespace.param('pipeline_id', 'pipeline_id')
class PipelineGetList(Resource):
    @namespace.doc('pipelines/post', security='Bearer', description='actions with pipeline')
    @namespace.expect(pipeline.pipeline_status_model)
    @namespace.response(200, 'Changed pipeline', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.response(404, 'Object not found', responses.error_response)
    @jwt_required()
    def post(self, pipeline_id):
        author = get_jwt_identity()

        item = PipelineService.select_pipeline(collection='pipeline', _key=pipeline_id, author=author)
        if not item:
            return {'success': False, 'message': f'pipeline with id: {pipeline_id} not found'}, 404

        pipelines = PipelineService.get_tree(pipeline_id=pipeline_id, author=author)
        jobs = PipelineService.get_jobs(pipelines, prefix=False)

        status_to_upd = {"status": TaskStatus.from_str(request.json['status'])}
        tasks = TaskService.update_tasks("in", data=status_to_upd, parent=jobs)

        return {'success': True, 'data': {"tasks": tasks}}, 200

    @namespace.doc('pipelines/get', security='Bearer', description='get full content for one pipeline')
    @namespace.response(200, 'Get pipeline and child as list', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.response(404, 'Object not found', responses.error_response)
    @jwt_required()
    def get(self, pipeline_id):
        author = get_jwt_identity()

        item = PipelineService.select_pipeline(collection='pipeline', _key=pipeline_id, author=author)
        if not item:
            return {'success': False, 'message': f'pipeline with id: {pipeline_id} not found'}, 404

        pipelines = PipelineService.get_tree(pipeline_id=pipeline_id, author=author)

        return {'success': True, 'data': {"pipelines": pipelines}}, 200

    @namespace.doc('pipeline/update', security='Bearer', description='update pipeline data')
    @namespace.expect(pipeline.pipeline_model)
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(200, 'Update pipeline', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.response(404, 'Object not found', responses.error_response)
    @jwt_required()
    def put(self, pipeline_id):
        author = get_jwt_identity()
        body = request.json

        item = PipelineService.select_pipeline(collection='pipeline', _key=pipeline_id, author=author)
        if not item:
            return {'success': False, 'message': f'pipeline with id: {pipeline_id} not found'}, 404

        item = PipelineService.update(collection='pipeline', id=pipeline_id, data=body)

        return {'success': True, 'data': item.to_json()}, 200

    @namespace.doc('pipeline/delete', security='Bearer', description='Delete a pipeline')
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(404, 'Object not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def delete(self, pipeline_id):
        author = get_jwt_identity()

        item = PipelineService.select_pipeline(
            collection='pipeline',
            _key=pipeline_id,
            author=author,
            one=True
        )
        if not item:
            return {'success': False, 'message': f'pipeline with id: {pipeline_id} not found'}, 404

        direction = PipelineService.select_pipeline(
            collection='pipeline_direction',
            pipeline=pipeline_id,
            author=author
        )
        children_to_delete = list(map(lambda row: row.get('_to'), direction)) \
            if direction \
            else []

        for child in reversed(children_to_delete):
            PipelineService.delete(_from=child, pipeline=pipeline_id)
            PipelineService.delete(_to=child, pipeline=pipeline_id)

        PipelineService.delete(collection='pipeline', _key=item.get('id'))
        PipelineService.delete(_to=item.get('_id'))

        return {'success': True}, 200


@namespace.route('/link/<string:pipeline_id>/<string:pipeline_job_id>')
@namespace.param('pipeline_job_id', 'pipeline or job id')
class PipelineDelete(Resource):
    @namespace.doc('pipeline_jobs/delete', security='Bearer', description='Delete connection or delete pipeline')
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(404, 'Object not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def delete(self, pipeline_id, pipeline_job_id):
        author = get_jwt_identity()
        item = PipelineService.select_pipeline(
            collection='pipeline',
            _key=pipeline_id,
            author=author,
            one=True
        )

        if not item:
            return {'success': False, 'message': 'pipeline not found'}, 404

        jobs = PipelineService.select_pipeline(
            _to=f'jobs/{pipeline_job_id}',
            pipeline=pipeline_id,
            author=author,
        )

        res = []
        for job in (jobs if jobs else []):
            res.append(PipelineService.recursion_query(job['_to'], {}, 0, pipeline_id))

        item.update({'jobs': res})
        children_to_delete = PipelineService.get_jobs(item.get('jobs'))

        for child in reversed(children_to_delete):
            PipelineService.delete(_from=child, pipeline=pipeline_id)
            PipelineService.delete(_to=child, pipeline=pipeline_id)

        return {'success': True}, 200


@namespace.route('/link/<string:parent_id>/<string:child_id>/<string:pipeline_id>')
@namespace.param('parent_id', 'parent id(job or pipeline)')
@namespace.param('child_id', 'child id only job')
@namespace.param('pipeline_id', 'pipeline id')
class PipelineConnect(Resource):
    @namespace.doc(
        'pipeline_jobs_connect_job/connect',
        security='Bearer',
        description='Second step connect between pipeline and created job or existed'
    )
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(404, 'Object not found', responses.error_response)
    @namespace.response(400, 'Bad request', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self, parent_id, child_id, pipeline_id):

        author = get_jwt_identity()
        if child_id == parent_id:
            return {'success': False, 'message': 'child and parent id can not be same'}, 400

        item = PipelineService.select_pipeline(
            collection='pipeline',
            _key=pipeline_id,
            author=author,
            one=True
        )

        if item is None:
            return {'success': False, 'message': 'pipeline not found'}, 404

        project_id = item['project']

        parent = PipelineService.select_pipeline(
            collection='pipeline',
            _key=parent_id,
            author=author,
            project=project_id,
            one=True
        )
        if not parent:
            parent = PipelineService.select_pipeline(
                collection='jobs',
                _key=parent_id,
                author=author,
                one=True
            )
            if not parent:
                return {'success': False, 'message': 'parent not found'}, 404

        child = PipelineService.select_pipeline(collection='jobs', _key=child_id, author=author, one=True)
        if not child:
            return {'success': False, 'message': 'child not found'}, 404

        connection = PipelineService.select_pipeline(
            collection='pipeline_direction',
            _to=child['_id'],
            author=author,
            project=project_id,
            pipeline=pipeline_id,
            one=False
        )
        if connection:
            return {'success': False, 'message': 'child already connected in this pipeline, remove connection first'}, 400

        link = {
            '_from': str(parent['_id']),
            '_to': str(child['_id']),
            'author': author,
            'project': str(project_id),
            'pipeline': str(pipeline_id)
        }
        data = PipelineService.insert(data=link, collection='pipeline_direction')
        return {'success': True, 'data': data}, 200


# get pipelines list with child's
@namespace.route('/copy')
class PipelineGet(Resource):
    @namespace.doc('pipeline/insert', security='Bearer', description='Copy pipeline')
    @namespace.expect(pipeline.pipeline_copy_model)
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(200, 'Created pipeline', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.response(404, 'Not Found', responses.error_response)
    @jwt_required()
    def post(self):

        body = request.json
        author = get_jwt_identity()

        def create_jobs(_job, _parent_id: str = "", _pipeline_id: str = "", _project_id: str = ""):
            if isinstance(_job, dict) and 'name' in _job.keys():
                _job['author'] = get_jwt_identity()
                _job.update(status=TaskStatus.pending_approval.value)
                if _job.get('params') is None:
                    _job['params'] = {}

                result = JobService.insert(_job)
                _from = _parent_id if 'jobs' in _parent_id else _pipeline_id
                _link = {
                    '_from': _from,
                    '_to': f'jobs/{str(result.id)}',
                    'author': author,
                    'project': _project_id,
                    'pipeline': _pipeline_id.replace('pipeline/', '')
                }
                data = PipelineService.insert(data=_link, collection='pipeline_direction')
                _parent_id = f'jobs/{result.id}'
                create_jobs(_job.get('jobs', []), _parent_id, _pipeline_id, _project_id)
            else:
                for one_job in _job:
                    create_jobs(one_job, _parent_id, _pipeline_id, _project_id)

        parent_id = body.get('parent_id')
        parent = PipelineService.select_pipeline(collection='pipeline', _key=parent_id, one=True)
        jobs = TemplateService.get_template_tree(pipeline_id=parent_id, author=author)

        if not parent:
            return {'success': False, 'message': 'parent pipeline not found'}, 404
        name = body.get('name')
        if not name:
            name = parent.get('name')

        data = {
            'name': name,
            'author': author,
            'complete': 0,
            'project': parent.get('project'),
        }

        item = PipelineService.insert(data, collection='pipeline').to_json()
        project_id = parent.get('project')
        link = {
            '_from': f'projects/{parent.get("project")}',
            '_to': item.get('_id'),
            'author': author,
            'project': project_id,
            'pipeline': item.get('id')
        }

        pipeline_direction = PipelineService.insert(link)

        for job in jobs:
            create_jobs(job['jobs'], parent_id, item.get('_id'), project_id)

        item.update({'nested': pipeline_direction.to_json()})

        return {'success': True, 'data': item}, 200
