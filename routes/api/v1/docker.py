# from models.Files import file
import spex_common.services.Docker as dockerService
import spex_common.services.Files as fileService
from flask_restx import Namespace, Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import responses


namespace = Namespace('Docker', description='Docker operations: start/stop/list/create/logs/delete')

namespace.add_model(responses.response.name, responses.response)
namespace.add_model(responses.error_response.name, responses.error_response)


@namespace.route('')
class DockerStartStop(Resource):
    @namespace.param('path', 'path to mount')
    @namespace.param('autoremove', 'autoremove True False', required=False)
    @namespace.doc('docker/startone', security='Bearer')
    # @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        path = request.args.get('path')
        auto_remove = bool(request.args.get('autoremove'))
        _path, folder = fileService.check_path(author, path)
        if _path is None:
            return {'success': False, 'message': f'path {path} not found'}, 200
        else:
            if folder:
                cont = dockerService.mount_and_start_container(author, _path, path, auto_remove=auto_remove)
                if cont is not None:
                    return {'success': True, 'container': cont.id}, 200
            else:
                return {'success': False, 'message': f'path {path} is file'}, 200


@namespace.route('/list')
class DockerListStatusDelete(Resource):
    @namespace.doc('docker/list', security='Bearer')
    @namespace.param('id', 'container id', required=False)
    # @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'containers not founded', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        id = request.args.get('id')
        if id is not None:
            listCont = dockerService.list_containers(author=author, id=id)
        else:
            listCont = dockerService.list_containers(author=author)
        arrdata = []
        for cont in listCont:
            data = {
                'id': cont.id,
                'status': cont.status,
                'name': cont.name
            }
            arrdata.append(data)
        return {'success': True, 'data': arrdata}, 200

    @namespace.doc('docker/delete', security='Bearer')
    @namespace.param('id', 'container id', required=False)
    # @namespace.marshal_with(_resource.list_tasks_response)
    @namespace.response(404, 'containers not founded', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required()
    def delete(self):
        author = get_jwt_identity()
        id = request.args.get('id')
        list_cont = []
        if id is not None:
            container = dockerService.list_containers(author=author, id=id)
            for cont in container:
                list_cont.append(cont)
                cont.remove()
        else:
            container = dockerService.list_containers(author=author)
            for cont in container:
                list_cont.append(cont)
                cont.remove()

        arrdata = []
        for cont in list_cont:
            data = {
                'id': cont.id,
                'status': cont.status,
                'name': cont.name
            }
            arrdata.append(data)
        return {'success': True, 'data': arrdata}, 200


@namespace.route('/start')
class DockerStart(Resource):
    @namespace.doc('docker/startbyid', security='Bearer')
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.param('id', 'container id')
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        id = request.args.get('id')
        container = dockerService.list_containers(author, id=id)
        if len(container) == 0:
            return {'success': False, 'message': f'docker container with id: {id} not found'}, 200
        elif len(container) > 1:
            return {'success': False, 'message': 'more than one container found'}, 200
        else:
            container[0].start()
        return {'success': True, 'container': container[0].id}, 200


@namespace.route('/stop')
class DockerStop(Resource):
    @namespace.doc('docker/stopbyid', security='Bearer')
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.param('id', 'container id')
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        id = request.args.get('id')
        container = dockerService.list_containers(author, id=id)
        if len(container) == 0:
            return {'success': False, 'message': f'docker container with id: {id} not found'}, 200
        elif len(container) > 1:
            return {'success': False, 'message': 'more than one container found'}, 200
        else:
            container[0].stop()
        return {'success': True, 'container': container[0].id}, 200


@namespace.route('/log')
class DockerLog(Resource):
    @namespace.doc('docker/logs', security='Bearer')
    @namespace.response(404, 'file not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @namespace.param('id', 'container id')
    @jwt_required()
    def get(self):
        author = get_jwt_identity()
        id = request.args.get('id')
        container = dockerService.list_containers(author, id=id)
        if len(container) == 0:
            return {'success': False, 'message': f'docker container with id: {id} not found'}, 200
        elif len(container) > 1:
            return {'success': False, 'message': 'more than one container found'}, 200
        else:
            log = (container[0].logs())
        return {'success': True, 'log': log.decode("utf-8")}, 200
