import spex_common.services.Templates as TemplateService
import spex_common.services.Pipeline as PipelineService
from flask_restx import Namespace, Resource
from flask import request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import templates as _templates
from .models import responses


namespace = Namespace('Templates', description='pipeline templates CRUD operations')

namespace.add_model(_templates.templates_model.name, _templates.templates_model)
namespace.add_model(_templates.templates_post_model.name, _templates.templates_post_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(_templates.a_templates_response.name, _templates.a_templates_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(_templates.list_templates_response.name, _templates.list_templates_response)
namespace.add_model(_templates.templates_get_model.name, _templates.templates_get_model)


# template result
@namespace.route('/<id>')
@namespace.param('id', 'get template by id')
class TemplateResGetPut(Resource):
    @namespace.doc('templates/getone', security='Bearer')
    @namespace.response(404, 'template not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.marshal_with(_templates.a_templates_response)
    @jwt_required()
    def get(self, id):

        template = TemplateService.select(id=id)
        if template is None:
            abort(404, 'template not found')

        return {'success': True, 'data': template.to_json()}, 200

    @namespace.doc('templates/updateone', security='Bearer')
    @namespace.marshal_with(_templates.a_templates_response)
    @namespace.expect(_templates.templates_model)
    @namespace.response(404, 'template not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def put(self, id):
        template = TemplateService.select(id=id)
        if template is None:
            abort(404, 'template not found')
        body = request.json
        template = TemplateService.update(id=id, data=body)

        return {'success': True, 'data': template.to_json()}, 200


@namespace.route('')
class TemplateResPost(Resource):
    @namespace.doc('templates/insertone', security='Bearer')
    @namespace.expect(_templates.templates_post_model)
    # @namespace.marshal_with(_history.list_history_response)
    @namespace.response(404, 'template not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        author = get_jwt_identity()
        body = request.json
        body["author"] = author
        pipeline_id = body["pipeline_source"]

        # template = TemplateService.insert(data=body)
        item = PipelineService.select_pipeline(collection='pipeline', _key=pipeline_id, author=author)
        if not item:
            return {'success': False, 'message': f'pipeline with id: {pipeline_id} not found'}, 404
        pipelines = PipelineService.get_tree(pipeline_id=pipeline_id, author=author)

        return {'success': True, 'data': pipelines}, 200

    @namespace.doc('template/getmany', security='Bearer')
    # @namespace.marshal_with(_template.list_template_response)
    # @namespace.response(200, 'list template current user', _template.list_template_response)
    @namespace.response(404, 'templates not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        result = TemplateService.select_template()

        if result is None:
            abort(404, 'template not found')

        return {'success': True, 'data': result}, 200
