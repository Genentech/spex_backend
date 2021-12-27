import spex_common.services.Pipeline as PipelineService
import spex_common.services.Project as ProjectService
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


# get pipelines list with child's
@namespace.route('s/<string:project_id>')
@namespace.param('project_id', 'project id')
class PipelineGet(Resource):
    @namespace.doc('pipelines/get', security='Bearer', description="get all project pipelines with children ")
    # @namespace.expect(projects.projects_model)
    # @namespace.marshal_with(projects.a_project_response)
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
    @namespace.doc('pipelines/get', security='Bearer', description='get full content for one pipeline')
    # @namespace.expect(projects.projects_model)
    # @namespace.marshal_with(projects.a_project_response)
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
    @namespace.doc('pipeline_jobs_connect_job/connect', security='Bearer', description='Second step connect between pipeline and created job or existed')
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(404, 'Object not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self, parent_id, child_id, pipeline_id):

        author = get_jwt_identity()
        if child_id == parent_id:
            return {'success': False, 'message': 'child and parent id can not be same'}
        _pipeline = PipelineService.select_pipeline(collection='pipeline', _key=pipeline_id, author=author, one=True)
        if _pipeline is None:
            return {'success': False, 'message': 'pipeline not found'}, 200
        project_id = _pipeline['project']

        _parent = PipelineService.select_pipeline(collection='pipeline', _key=parent_id, author=author, project=project_id, one=True)
        if _parent is None:
            _parent = PipelineService.select_pipeline(collection='jobs', _key=parent_id, author=author, one=True)
            if _parent is None:
                return {'success': False, 'message': 'parent not found'}, 200

        _child = PipelineService.select_pipeline(collection='jobs', _key=child_id, author=author, one=True)
        if _child is None:
            return {'success': False, 'message': 'child not found'}, 200

        if lines := PipelineService.select_pipeline(collection='pipeline_direction', _to=_child['_id'], author=author, project=project_id, pipeline=pipeline_id, one=False):
            return {'success': False, 'message': 'child already connected in this pipeline, remove connection first'}, 200
            # PipelineService.delete(collection='pipeline_direction', _to=_child['_id'], author=author, project=project_id)

        ft = {'_from': str(_parent['_id']),
              '_to': str(_child['_id']),
              'author': author,
              'project': str(project_id),
              'pipeline': str(pipeline_id)}
        data = PipelineService.insert(data=ft, collection='pipeline_direction')
        return {'success': True, 'data': data}, 200
