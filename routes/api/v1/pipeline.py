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
namespace.add_model(pipeline.task_resource_image_connect_to_box.name, pipeline.task_resource_image_connect_to_box)


def recursion_query(itemid, tree, depth):

    text = 'FOR d IN box ' + \
          f'FILTER d._id == "{itemid}" ' + \
           'LET boxes = (' + \
          f'FOR b IN 1..1 OUTBOUND "{itemid}"' + ' GRAPH "pipeline" FILTER b._id LIKE "box/%"  RETURN {"name": b.name, "id": b._key, "status": b.complete } )' + \
           'LET resources = (' + \
          f'FOR b IN 1..1 INBOUND "{itemid}"' + ' GRAPH "pipeline" FILTER b._id LIKE "resource/%"  RETURN {"name": b.name, "id": b._key, "status": 0 } )' + \
           'LET tasks = (' + \
          f'FOR t IN 1..1 INBOUND "{itemid}"' + ' GRAPH "pipeline" FILTER t._id LIKE "tasks/%" RETURN {"name": t.name, "id": t._key, "status": t.status } )' + \
           ' RETURN MERGE({"id": d._key, "name": d.name, "status": d.complete}, {"boxes": boxes, "tasks": tasks, "resources": resources})'

    result = db_instance().query(text)
    if len(result) > 0:
        tree = result[0]
    else:
        return

    i = 0
    if depth < 50:
        if (result[0]['boxes'] is not None and len(result[0]['boxes']) > 0):
            while i < len(result[0]['boxes']):
                id = 'box/' + str(result[0]['boxes'][i]['id'])
                tree['boxes'][i] = recursion_query(id, tree['boxes'][i], depth + 1)
                i += 1
    return tree


def depth(x):
    if type(x) is dict and x:
        return 1 + max(depth(x[a]) for a in x)
    if type(x) is list and x:
        return 1 + max(depth(a) for a in x)
    return 0


def getBoxes(x):
    boxes = []
    if type(x) is list and x:
        for box in x:
            if box is None:
                return boxes
            boxes.append(box.get('id'))
            if box.get('boxes') is not None:
                boxes = boxes + getBoxes(box.get('boxes'))
    return boxes


def searchInArrDict(key, value, arr):
    founded = []
    for item in arr:
        item_value = item.get(key)
        if value is not None and item_value == value:
            founded.append(arr.index(item))
    return founded


# directions between pipelines boxes tasks
@namespace.route('/<string:project_id>/<string:parent_id>')
@namespace.param('project_id', 'project id')
@namespace.param('parent_id', 'who is daddy')
class PipelineCreatePost(Resource):
    @namespace.doc('pipeline_directions/insert', security='Bearer')
    @namespace.expect(pipeline.task_resource_image_connect_to_box)
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
        b_id_arr = body.get('box_ids')
        project = ProjectService.select(project_id)
        if t_id_arr is not None:
            notFoundedInProject = list(set(t_id_arr) - set(project.taskIds))
            if len(notFoundedInProject) > 0:
                message = f'tasks with ids: {notFoundedInProject} not found in project data'
                return {'success': False, "message": message}, 200

        if r_id_arr is not None:
            notFoundedInProject = list(set(r_id_arr) - set(project.resource_ids))
            if len(notFoundedInProject) > 0:
                message = f'resource with ids: {notFoundedInProject} not found in project data'
                return {'success': False, "message": message}, 200

        parent = PipelineService.select_pipeline(collection='pipeline', _key=parent_id, author=author, project=project_id, one=True)
        if parent is None:
            parent = PipelineService.select_pipeline(collection='box', _key=parent_id, author=author, project=project_id, one=True)
            if parent is None:
                message = f'box or pipeline with id: {parent_id} not found'
                return {'success': False, "message": message}, 200
        foundedT = []
        if t_id_arr is not None:
            foundedT = TaskService.select_tasks(condition='in', _key=t_id_arr)
            if foundedT is None:
                foundedT = []
                message = f'tasks not found {t_id_arr}'
                return {'success': False, "message": message}, 200
        foundedR = []
        if r_id_arr is not None:
            foundedR = JobService.select_jobs(condition='in', _key=r_id_arr, collection='resource')
            if foundedR is None:
                foundedR = []
                message = f'resources not found {r_id_arr}'
                return {'success': False, "message": message}, 200
        foundedB = []
        if b_id_arr is not None:
            foundedB = PipelineService.select_pipeline(collection='box', _key=b_id_arr, condition='in', author=[author])
            if foundedB is None:
                message = f'boxes not found {b_id_arr}'
                foundedB = []
                return {'success': False, "message": message}, 200

        foundedC = list(foundedT + foundedR + foundedB)
        arr_founded_id = []
        existed = []
        for item in foundedC:
            c_id = item.get('id')
            f_t = {}
            f_t.update({'_from': str(item.get('_id'))})
            f_t.update({'_to': 'box/'+str(parent_id)})
            f_t.update({'author': author})
            f_t.update({'project': project_id})
            has = PipelineService.select_pipeline(_from=str(str(item.get('_id'))), _to='box/'+str(parent_id), author=author, project=project_id)
            if has is None:
                PipelineService.insert(f_t)
                arr_founded_id.append(c_id)
            else:
                existed.append(c_id)

        notFoundedC = list(set(t_id_arr if t_id_arr is not None else []) - set(arr_founded_id if arr_founded_id is not None else []) - set(existed if existed is not None else []))
        result = {'Added': arr_founded_id, 'NotFounded': notFoundedC, 'Existed': existed}

        return {'success': True, 'data': result}, 200
# directions between pipelines boxes tasks


# get pipelines list with child's
@namespace.route('/<string:project_id>')
@namespace.param('project_id', 'project id')
class PipelineGet(Resource):
    @namespace.doc('pipelines/get', security='Bearer')
    # @namespace.expect(projects.projects_model)
    # @namespace.marshal_with(projects.a_project_response)
    @namespace.response(200, 'Get pipeline and childs', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self, project_id):

        author = get_jwt_identity()
        if ProjectService.select_projects(_key=project_id, author=author) is None:
            return {'success': False, 'message': f'project with id: {project_id} not found'}, 200

        pipelines = PipelineService.select_pipeline(collection='pipeline', author=author, project=project_id)
        result = None
        lines = []
        if pipelines is None:
            return {'success': True, 'data': {"pipelines": lines}}, 200
        for pipeline_ in pipelines:
            res = []
            boxes = PipelineService.select_pipeline(author=author, _from=pipeline_.get('_id'))
            if boxes is None:
                pipeline_.pop('_from', None)
                pipeline_.pop('_to', None)
                pipeline_.update({'boxes': res})
                lines.append(pipeline_)
                continue
            for box in boxes:
                res.append(recursion_query(box['_to'], {}, 0))
            pipeline_.pop('_from', None)
            pipeline_.pop('_to', None)
            pipeline_.update({'boxes': res})
            lines.append(pipeline_)

        result = {"pipelines": lines}

        return {'success': True, 'data': result}, 200


# get pipeline with childs
@namespace.route('/path/<string:project_id>/<string:pipeline_id>')
@namespace.param('project_id', 'project id')
@namespace.param('pipeline_id', 'pipeline_id')
class PipelineGetList(Resource):
    @namespace.doc('pipelines/get', security='Bearer')
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

        pipelines = PipelineService.select_pipeline(collection='pipeline', author=author, project=project_id, _key=pipeline_id)

        lines = []
        if pipelines is None:
            return {'success': True, 'data': {"pipelines": lines}}, 200
        for pipeline_ in pipelines:
            res = []
            boxes = PipelineService.select_pipeline(author=author, _from=pipeline_.get('_id'))
            if boxes is None:
                pipeline_.pop('_from', None)
                pipeline_.pop('_to', None)
                pipeline_.update({'boxes': res})
                lines.append(pipeline_)
                continue
            for box in boxes:
                res.append(recursion_query(box['_to'], {}, 0))
            pipeline_.pop('_from', None)
            pipeline_.pop('_to', None)
            pipeline_.update({'boxes': res})
            lines.append(pipeline_)

        result = {"pipelines": lines}

        return {'success': True, 'data': result}, 200


# insert new box to another box, or to pipeline
@namespace.route('/box/<string:project_id>/<string:parent_id>')
@namespace.param('project_id', 'project id')
@namespace.param('parent_id', 'who is daddy pipeline or another box')
class BoxCreate(Resource):
    @namespace.doc('box/insert', security='Bearer')
    @namespace.expect(pipeline.pipeline_model)
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(200, 'Created box', pipeline.a_pipeline_response)
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
            parent = PipelineService.select(id=parent_id, collection='box', to_json=True, one=True)
            if parent is None:
                return {'success': False, 'message': f'box or pipeline with id: {parent_id} not found'}, 200

        data = {'name': body.get('name')}
        data.update({'author': author})
        data.update({'complete': 0})
        data.update({'project': project_id})
        data.update({'parent': parent_id})
        box = PipelineService.insert(data, collection='box')
        if box is not None:
            box = box.to_json()
        f_t = {}
        f_t.update({'_from': parent.get('_id')})
        f_t.update({'_to': box.get('_id')})
        f_t.update({'author': author})
        f_t.update({'project': project_id})
        f_t.update({'parent': parent_id})
        pipeline = PipelineService.insert(f_t)
        box.update({'nested': pipeline.to_json()})

        return {'success': True, 'data': box}, 200
# insert new box to another box, or to pipeline


# insert pipeline to project
@namespace.route('/create/<string:project_id>')
@namespace.param('project_id', 'project id')
class PipelineCreate(Resource):
    @namespace.doc('pipeline/insert', security='Bearer')
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
        pipeline = PipelineService.insert(data, collection='pipeline')
        f_t = {}
        f_t.update({'_from': 'projects/'+project_id})
        f_t.update({'_to': pipeline._id})
        f_t.update({'author': author})
        f_t.update({'project': project_id})
        pipeline_direction = PipelineService.insert(f_t)
        pipeline = pipeline.to_json()
        pipeline.update({'nested': pipeline_direction.to_json()})

        return {'success': True, 'data': pipeline}, 200
# insert pipeline to project


# update pipeline data
@namespace.route('/update/<string:project_id>/<string:pipeline_box_id>')
@namespace.param('project_id', 'project id')
@namespace.param('pipeline_box_id', 'pipeline or box id')
class PipelineBoxUpdate(Resource):
    @namespace.doc('pipeline/update', security='Bearer')
    @namespace.expect(pipeline.pipeline_model)
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(200, 'Update pipeline', pipeline.a_pipeline_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def put(self, project_id, pipeline_box_id):
        author = get_jwt_identity()
        body = request.json
        if ProjectService.select_projects(_key=project_id, author=author) is None:
            return {'success': False, 'message': 'project not found'}, 200

        if PipelineService.select_pipeline(collection='pipeline', _key=pipeline_box_id, author=author, project=project_id) is not None:
            pipeline_ = PipelineService.update(collection='pipeline', id=pipeline_box_id, data=body)
        else:
            if PipelineService.select_pipeline(collection='box', _key=pipeline_box_id, author=author, project=project_id) is None:
                return {'success': False, 'message': 'pipeline or box not found'}, 200
            else:
                pipeline_ = PipelineService.update(collection='box', id=pipeline_box_id, data=body)

        return {'success': True, 'data': pipeline_.to_json()}, 200
# update pipeline data


@namespace.route('/delete/<string:project_id>/<string:pipeline_id>')
@namespace.param('project_id', 'project id')
@namespace.param('pipeline_id', 'pipeline id')
class PipelineDelete(Resource):
    @namespace.doc('pipeline_boxes/delete', security='Bearer')
    @namespace.marshal_with(pipeline.a_pipeline_response)
    @namespace.response(404, 'Object not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def delete(self, project_id, pipeline_id):
        author = get_jwt_identity()
        project = ProjectService.select_projects(_key=project_id, author=author)   # only author projects show
        if project is None:
            return {'success': False, 'message': 'project not found'}, 200
        pipeline_ = PipelineService.select_pipeline(collection='pipeline', _key=pipeline_id, author=author, project=project_id, one=True)
        if pipeline_ is None:
            pipeline_ = PipelineService.select_pipeline(collection='box', _key=pipeline_id, author=author, project=project_id, one=True)
            if pipeline_ is None:
                return {'success': False, 'message': 'pipeline not found'}, 200

        boxes = PipelineService.select_pipeline(author=author, _from=pipeline_.get('_id'))
        res = []
        if boxes is not None:
            for box in boxes:
                res.append(recursion_query(box['_to'], {}, 0))

        pipeline_.update({'boxes': res})
        childs_to_delete = getBoxes(pipeline_.get('boxes'))
        for child in reversed(childs_to_delete):
            PipelineService.delete(_from=child)
            PipelineService.delete(_to=child)
            PipelineService.delete(collection='box', _key=child)
        PipelineService.delete(collection=pipeline_.get('_id').replace('/'+pipeline_.get('id'), ''), _key=pipeline_.get('id'))
        PipelineService.delete(_to=pipeline_.get('_id'))
        return {'success': True, 'data': pipeline_}, 200
