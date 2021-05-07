import services.Pipeline as PipelineService
import services.Task as TaskService
from flask_restx import Namespace, Resource
from flask import request, abort
# from models.Job import Job
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import pipeline, responses

namespace = Namespace('Pipeline', description='Pipeline CRUD operations')

namespace.add_model(pipeline.pipeline_model.name, pipeline.pipeline_model)
namespace.add_model(pipeline.box_model.name, pipeline.box_model)
namespace.add_model(pipeline.pipeline_post_model.name, pipeline.pipeline_post_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(pipeline.a_pipeline_response.name, pipeline.a_pipeline_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(pipeline.list_pipeline_response.name, pipeline.list_pipeline_response)
namespace.add_model(pipeline.pipeline_get_model.name, pipeline.pipeline_get_model)


@namespace.route('/')
class PipelineCreateGetPost(Resource):
    @namespace.doc('pipeline/insert')
    @namespace.expect(pipeline.pipeline_model)
    # @namespace.marshal_with(projects.a_project_response)
    @namespace.response(200, 'Created project', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        body = request.json
        author = get_jwt_identity()
        p_id = body.get('parent_id')
        c_id_arr = body.get('child_ids')
        parent = PipelineService.select(id=p_id, collection='box')
        if parent is None:
            abort(404, f'box with id: {p_id} not found')
        foundedC = TaskService.select_tasks(condition='in', _id=c_id_arr)
        if foundedC is None:
            abort(404, 'childs not found')

        arr_founded_id = []
        for item in foundedC:
            c_id = item.get('_id')
            arr_founded_id.append(c_id)
            f_t = {}
            f_t.update({'_from': str(c_id)})
            f_t.update({'_to': 'box/'+str(p_id)})
            f_t.update({'author': author})
            has = PipelineService.select_pipeline(_from=str(c_id), _to='box/'+str(p_id), author=author)
            if has is None:
                PipelineService.insert(f_t)
        notFoundedC = list(set(c_id_arr) - set(arr_founded_id))
        result = {'Added': arr_founded_id, 'NotFounded': notFoundedC}

        return {'success': True, 'data': result}, 200

    @namespace.doc('box/get')
    # @namespace.expect(projects.projects_model)
    # @namespace.marshal_with(projects.a_project_response)
    @namespace.response(200, 'Get pipeline and childs', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        boxes = PipelineService.select_pipeline(condition='LIKE', author=author, _from='%box%', _to='%box%')
        arr_boxes = []
        for edge in boxes:
            arr_boxes.append(edge.get('parent'))
            arr_boxes.append(edge.get('child'))
        

        return {'success': True, 'author': author}, 200


@namespace.route('/box')
class BoxCreateGetPost(Resource):
    @namespace.doc('box/insert')
    @namespace.expect(pipeline.box_model)
    # @namespace.marshal_with(projects.a_project_response)
    @namespace.response(200, 'Created box', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        body = request.json
        author = get_jwt_identity()
        new = True
        p_id = body.get('parent_id')
        parent = None
        name = body.get('name')

        data = {'name': name}
        data.update({'author': author})
        if p_id is not None:
            new = False
            parent = PipelineService.select(id=p_id, collection='box')
            if parent is None:
                abort(404, f'box with id: {p_id} not found')
            # else:
            #     childs = PipelineService.select_pipeline_edge(parent.id)

        data.update({'complete': 0})
        box = PipelineService.insert(data, collection='box')
        if box is not None:
            box = box.to_json()
        if not new:
            f_t = {}
            f_t.update({'_from': parent._id})
            f_t.update({'_to': box.get('_id')})
            f_t.update({'author': author})
            pipeline = PipelineService.insert(f_t)
            box.update({'nested': pipeline.to_json()})

        return {'success': True, 'data': box}, 200
