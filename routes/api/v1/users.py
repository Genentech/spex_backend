import services.User as UserService
import datetime
from flask_restx import Namespace, Resource
from flask import request, abort
from models.User import User
from flask_jwt_extended import create_access_token
from .models import users, responses

namespace = Namespace('Users', description='Users CRUD operations')

namespace.add_model(users.user_model.name, users.user_model)
namespace.add_model(users.user_get_model.name, users.user_get_model)
namespace.add_model(users.signup_model.name, users.signup_model)
namespace.add_model(users.login_model.name, users.login_model)
namespace.add_model(responses.response.name, responses.response)
namespace.add_model(users.a_user_response.name, users.a_user_response)
namespace.add_model(users.list_user_response.name, users.list_user_response)
namespace.add_model(responses.error_response.name, responses.error_response)


@namespace.route('/')
class Items(Resource):
    @namespace.doc('users/singup')
    @namespace.expect(users.signup_model)
    @namespace.marshal_with(users.a_user_response)
    @namespace.response(200, 'Created user', users.a_user_response)
    @namespace.response(400, 'Message about reason of error', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    def post(self):
        # TODO check JWT, return error 401
        body = request.json
        email = body['email']
        password = body['password']
        confirmation = body['confirmation']

        if not User.valid_email(email):
            abort(400, 'Incorrect email: {}'.format(email))

        has_user = UserService.select_user(email)
        if has_user:
            abort(400, 'User with email {} already exists'.format(email))

        if password != confirmation:
            abort(400, 'Password and confirmation don\'t match')

        body = User.hash_password(body)
        result = UserService.insert(body)
        return {'success': True, 'data': result}, 200

    @namespace.doc('users/list')
    @namespace.marshal_list_with(users.list_user_response)
    @namespace.response(200, 'List of users', users.list_user_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    def get(self):
        # TODO check JWT, return error 401
        items = UserService.select_users()
        return {'success': True, 'data': items}, 200


@namespace.route('/login')
class Login(Resource):
    @namespace.doc('users/login')
    @namespace.expect(users.login_model)
    @namespace.marshal_with(users.a_user_response)
    @namespace.header('Authorization', 'JWT token')
    @namespace.response(200, 'Created user', users.a_user_response)
    @namespace.response(404, 'User not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    def post(self):
        body = request.json
        user = UserService.select_user(body['email'])
        if user is None:
            abort(404, 'User with {} email address not found'.format(body['email']))

        authorized = user.check_password(body['password'])

        if not authorized:
            abort(401, 'Unable to login user')

        expires = datetime.timedelta(days=1)
        access_token = create_access_token(identity=str(user.id), expires_delta=expires)
        return {'success': True, 'data': user}, 200, \
               {'Authorization': access_token}


@namespace.route('/<string:id>')
class Item(Resource):
    @namespace.doc('user')
    @namespace.marshal_with(users.a_user_response)
    @namespace.response(404, 'User not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    def get(self, id):
        # TODO check JWT, return error 401
        if id == 'login':
            abort(404, 'User with id:{} not found'.format(id))

        user = UserService.select_user(id=id)

        if user is None:
            abort(404, 'User with id:{} not found'.format(id))

        return {'success': True, 'data': user}, 200

    @namespace.doc('user/update')
    @namespace.marshal_with(users.a_user_response)
    @namespace.response(200, 'Updated user', users.a_user_response)
    @namespace.response(404, 'User not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    def put(self, id):
        # TODO check JWT, return error 401
        #  add UserService.update(id, data). Users can't change email,
        #  for password (old password, new, and confirm new)
        abort(500, 'Not implemented')

    @namespace.doc('user/delete')
    @namespace.marshal_with(responses.response)
    @namespace.response(204, 'User deleted')
    @namespace.response(404, 'User not found', responses.error_response)
    @namespace.response(401, 'Unauthorized', responses.error_response)
    def delete(self, id):
        # TODO check JWT, return error 401
        #  add UserService.delete(id), only admins can remove users,
        #  need add to jwt role, and in user model
        abort(500, 'Not implemented')
