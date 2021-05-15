import services.Pipeline as PipelineService
import services.Task as TaskService
from flask_restx import Namespace, Resource
from flask import request
# from models.Job import Job
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import pipeline, responses
from modules.database import database

namespace = Namespace('Pipeline', description='Pipeline CRUD operations')

namespace.add_model(pipeline.pipeline_model.name, pipeline.pipeline_model)
namespace.add_model(pipeline.box_model.name, pipeline.box_model)
namespace.add_model(pipeline.pipeline_post_model.name, pipeline.pipeline_post_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(pipeline.a_pipeline_response.name, pipeline.a_pipeline_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(pipeline.list_pipeline_response.name, pipeline.list_pipeline_response)
namespace.add_model(pipeline.pipeline_get_model.name, pipeline.pipeline_get_model)


def recursionQuery(itemId, tree, depth):

    text = 'FOR d IN box ' + \
          f'FILTER d._id == "{itemId}" ' + \
           'LET boxes = (' + \
          f'FOR b IN 1..1 OUTBOUND "{itemId}"' + ' GRAPH "pipeline" FILTER b._id LIKE "box/%"  RETURN {"name": b.name, "id": b._key, "status": b.complete } )' + \
           'LET tasks = (' + \
          f'FOR t IN 1..1 INBOUND "{itemId}"' + ' GRAPH "pipeline" FILTER t._id LIKE "tasks/%" RETURN {"name": t.name, "id": t._key, "status": t.status } )' + \
           ' RETURN MERGE({"id": d._key, "name": d.name, "status": d.complete}, {"boxes": boxes, "tasks": tasks})'

    result = database.query(text)
    if len(result) > 0:
        tree = result[0]
    else:
        return

    i = 0
    if depth < 10:
        if (result[0]['boxes'] is not None and len(result[0]['boxes']) > 0):
            while i < len(result[0]['boxes']):
                id = 'box/' + str(result[0]['boxes'][i]['id'])
                tree['boxes'][i] = recursionQuery(id, tree['boxes'][i], depth + 1)
                i += 1
    return tree


def searchInArrDict(key, value, arr):
    founded = []
    for item in arr:
        item_value = item.get(key)
        if value is not None and item_value == value:
            founded.append(arr.index(item))
    return founded


@namespace.route('')
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
            message = f'box with id: {p_id} not found'
            return {'success': False, message: message}, 200
        foundedC = TaskService.select_tasks(condition='in', _key=c_id_arr)
        if foundedC is None:
            foundedC = PipelineService.select_pipeline(collection='box', condition='in', _key=c_id_arr)
            if foundedC is None:
                message = 'childs not found'
                return {'success': False, message: message}, 200

        arr_founded_id = []
        existed = []
        for item in foundedC:
            c_id = item.get('id')
            f_t = {}
            f_t.update({'_from': str(item.get('_id'))})
            f_t.update({'_to': 'box/'+str(p_id)})
            f_t.update({'author': author})
            has = PipelineService.select_pipeline(_from=str(str(item.get('_id'))), _to='box/'+str(p_id), author=author)
            if has is None:
                PipelineService.insert(f_t)
                arr_founded_id.append(c_id)
            else:
                existed.append(c_id)

        notFoundedC = list(set(c_id_arr) - set(arr_founded_id) - set(existed))
        result = {'Added': arr_founded_id, 'NotFounded': notFoundedC, 'Existed': existed}

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
        pipe_boxes = PipelineService.select_pipeline(condition='LIKE', author=author, _from='%box%', _to='%box%')
        result = None
        lines = []
        for box in pipe_boxes:
            box_copy = pipe_boxes.copy()
            box_copy.remove(box)
            if len(searchInArrDict('_to', box['_from'], box_copy)) == 0:
                lines.append(box)
        arrLines = []
        for box in lines:
            arrLines.append(recursionQuery(box['_from'], {}, 0))

        result = {"pipelines": arrLines}

        return {'success': True, 'data': result}, 200


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
                return {'success': True, 'message': f'box with id: {p_id} not found'}, 200

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
