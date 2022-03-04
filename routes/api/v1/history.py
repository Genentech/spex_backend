import spex_common.services.History as HistService
from flask_restx import Namespace, Resource
from flask import request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import history as _history
from .models import responses


namespace = Namespace('History', description='logs and changes CRUD operations')

namespace.add_model(_history.history_model.name, _history.history_model)
namespace.add_model(_history.history_post_model.name, _history.history_post_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(_history.a_history_response.name, _history.a_history_response)
namespace.add_model(responses.error_response.name, responses.error_response)
namespace.add_model(_history.list_history_response.name, _history.list_history_response)
namespace.add_model(_history.history_get_model.name, _history.history_get_model)


# history result
@namespace.route('/<id>')
@namespace.param('id', 'history id')
class HistoryResGetPut(Resource):
    @namespace.doc('history/getone', security='Bearer')
    @namespace.response(404, 'history not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.marshal_with(_history.a_history_response)
    @jwt_required()
    def get(self, id):
        history = HistService.select(id=id)
        if history is None:
            abort(404, 'history not found')

        return {'success': True, 'data': history.to_json()}, 200

    @namespace.doc('history/updateone', security='Bearer')
    @namespace.marshal_with(_history.a_history_response)
    @namespace.expect(_history.history_model)
    @namespace.response(404, 'history not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def put(self, id):
        history = HistService.select(id=id)
        if history is None:
            abort(404, 'history not found')
        body = request.json
        history = HistService.update(id=id, data=body)

        return {'success': True, 'data': history.to_json()}, 200


@namespace.route('')
class HistoryResPost(Resource):
    @namespace.doc('history/insertone', security='Bearer')
    @namespace.expect(_history.history_post_model)
    # @namespace.marshal_with(_history.list_history_response)
    @namespace.response(404, 'history not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):
        author = get_jwt_identity()
        body = request.json
        body["author"] = author

        history = HistService.insert(data=body)

        return {'success': True, 'data': history.to_json()}, 200

    @namespace.doc('history/getmany', security='Bearer')
    @namespace.marshal_with(_history.list_history_response)
    @namespace.response(200, 'list history current user', _history.list_history_response)
    @namespace.response(404, 'history not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        result = HistService.select_history(author=author)

        if result is None:
            abort(404, 'history not found')

        return {'success': True, 'data': result}, 200
