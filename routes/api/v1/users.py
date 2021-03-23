import services.User as UserService
import datetime
import modules.omeroweb as omeroweb

from flask_restx import Namespace, Resource
from flask import request, abort
from flask_jwt_extended import \
    create_access_token, \
    jwt_required, \
    get_jwt_identity
from .models import users, responses

namespace = Namespace('Users', description='Users CRUD operations')

namespace.add_model(users.user_model.name, users.user_model)
namespace.add_model(users.user_get_model.name, users.user_get_model)
namespace.add_model(users.login_model.name, users.login_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(users.a_user_response.name, users.a_user_response)
namespace.add_model(users.list_user_response.name, users.list_user_response)
namespace.add_model(responses.error_response.name, responses.error_response)


def merge_user_and_omero_user(user, omero_user):
    return {
        **user.to_json(),
        'email': omero_user['email'] if 'email' in omero_user else '',
        'firstName': omero_user['FirstName'],
        'lastName': omero_user['LastName']
    }


@namespace.route('/')
class Items(Resource):
    @namespace.doc('users/list')
    @namespace.marshal_list_with(users.list_user_response)
    @namespace.response(200, 'List of users', users.list_user_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required(locations=['headers'])
    def get(self):
        items = UserService.select_users()
        return {'success': True, 'data': items}, 200


@namespace.route('/login')
class Login(Resource):
    @namespace.doc('users/login')
    @namespace.expect(users.login_model)
    @namespace.marshal_with(users.a_user_response)
    @namespace.header('Authorization', 'JWT token')
    @namespace.response(200, 'Logged user', users.a_user_response)
    @namespace.response(404, 'User not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    def post(self):
        body = request.json

        login = body['username']
        password = body['password']
        client = omeroweb.create(login, password)
        if not client:
            abort(401, 'Unable to login user')

        user_id = client.omero_context['userId']

        url = f'/api/v0/m/experimenters/{user_id}'

        omero_user = client.get(url)

        if not omero_user or omero_user.status_code != 200:
            abort(401, 'Unable to login user')

        omero_user = omero_user.json()['data']

        user = UserService.select(login)
        if user is None:

            user = {
                'username': omero_user['UserName'],
                'omeroUserId': omero_user['@id'],
            }

            user = UserService.insert(user)

        user = merge_user_and_omero_user(user, omero_user)

        expires = datetime.timedelta(days=7)
        identity = {
            'login': login,
            'id': user['id'],
        }
        access_token = create_access_token(identity, expires_delta=expires)

        return {'success': True, 'data': user}, 200, \
               {'Authorization': access_token}


@namespace.route('/<string:id>')
class Item(Resource):
    @namespace.doc('user/get')
    @namespace.marshal_with(users.a_user_response)
    @namespace.response(404, 'User not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required(locations=['headers'])
    def get(self, id):
        if id == 'login':
            abort(404, f'User with id:{id} not found')

        current_user = get_jwt_identity()
        login = current_user['login']

        client = omeroweb.get(login)

        if not client:
            abort(401, 'Unauthorized')

        user = UserService.select(id=id)

        if user is None:
            abort(404, f'User with id:{id} not found')

        omero_user = client.get(f'/api/v0/m/experimenters/{user.omeroUserId}')

        if not omero_user or omero_user.status_code != 200:
            abort(404, f'User with id:{id} not found')

        omero_user = omero_user.json()['data']

        user = merge_user_and_omero_user(user, omero_user)

        return {'success': True, 'data': user}, 200

    @namespace.doc('user/delete')
    @namespace.marshal_with(responses.response)
    @namespace.response(204, 'User deleted')
    @namespace.response(404, 'User not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    @jwt_required(locations=['headers'])
    def delete(self, id):

        current_user = get_jwt_identity()

        if current_user['id'] != id and not UserService.isAdmin(current_user):
            abort(401, 'only admins can remove users')

        user = UserService.delete(id=id)
        if user is None:
            abort(404, f'User with id:{id} not deleted')

        return {'success': True, 'data': user}, 200
