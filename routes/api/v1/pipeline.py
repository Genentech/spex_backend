import services.Pipeline as PipelineService
import services.Task as TaskService
from flask_restx import Namespace, Resource
from flask import request, abort
# from models.Job import Job
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import pipeline, responses

namespace = Namespace('Pipeline', description='Pipeline CRUD operations')

namespace.add_model(pipeline.pipeline_model.name, pipeline.pipeline_model)
namespace.add_model(pipeline.pipeline_post_model.name, pipeline.pipeline_post_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(pipeline.a_pipeline_response.name, pipeline.a_pipeline_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(pipeline.list_pipeline_response.name, pipeline.list_pipeline_response)
namespace.add_model(pipeline.pipeline_get_model.name, pipeline.pipeline_get_model)


@namespace.route('/')
class PipelineCreateGetPost(Resource):
    @namespace.doc('pipeline/insert')
    # @namespace.expect(projects.projects_model)
    # @namespace.marshal_with(projects.a_project_response)
    @namespace.response(200, 'Created project', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        body = request.json
        body['author'] = get_jwt_identity()
        p_id = body.get('parent_id')
        c_id = body.get('child_id')
        name = body.get('name')
        new = body.get('new')

        parent = TaskService.select(p_id)
        f_t = {}
        f_t.update({'_from': 'tasks/'+str(p_id)})
        if parent is None:
            parent = PipelineService.select(p_id)
            if parent is None:
                abort(404, f'task with id: {p_id} not found')
            f_t.update({'_from': 'pipeline/'+str(p_id)})

        child = TaskService.select(c_id)
        if child is None:
            abort(404, f'task with id: {c_id} not found')

        f_t.update({'_to': 'tasks/'+str(c_id)})

        if new is True:
            f_t.update({'new': new})
        f_t.update({'startnext': 0})
        if name is not None:
            f_t.update({'name': name})
        pipeline = PipelineService.insert(f_t)

        data = {}
        data.update({'parent': parent.to_json()})
        data.update({'child': child.to_json()})
        data.update({'pipe': pipeline.to_json()})
        return {'success': True, 'data': data}, 200
