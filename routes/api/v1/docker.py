# from models.Files import file
import services.Docker as dockerService
import services.Files as fileService
from flask_restx import Namespace, Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import responses


namespace = Namespace('Docker', description='Docker operations: start/stop/list/create/logs/delete')

namespace.add_model(responses.response.name, responses.response)
namespace.add_model(responses.error_response.name, responses.error_response)


@namespace.route('')
class DockerListStartStop(Resource):
    @namespace.param('path', 'path to mount')
    @namespace.doc('resource/startone', security='Bearer')
    # @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        path = request.args.get('path')
        _path, folder = fileService.check_path(author, path)
        if _path is None:
            return {'success': False, 'message': f'path {path} not found'}, 200
        else:
            if folder:
                cont = dockerService.mountAndStartContainer(author, _path)
                if cont is not None:
                    return {'success': True, 'container': cont.id}, 200
            else:
                return {'success': False, 'message': f'path {path} is file'}, 200

    @namespace.doc('resource/getfiletree', security='Bearer')
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def post(self):

        return {'success': 'True'}, 200
