from flask_restx import Namespace, Resource, fields
from flask import request
from database import database
from validation import User
from flask_jwt_extended import create_access_token
import datetime


register = Namespace('register', description='User registration')
register_model = register.model('register', {
    'email': fields.String(required=True, description='email and key'),
    'password': fields.String(required=True,  description='User password', help="password cannot be empty."),
    'firstName': fields.String(required=True,  description='Firstname', help="First name cannot be empty."),
    'lastName': fields.String(required=True,  description='Lastname', help="Lastname cannot be empty."),
    'confirmation': fields.String(required=True,  description='Confirmation', help="Confirmation password cannot be empty.")
})

users_list = Namespace('userdata', description='User list')
users_get_model = users_list.model('user list', {'email': fields.String(required=True, description='email and key')})


login = Namespace('login', description='User login')
login_model = login.model('user login', {'email': fields.String(required=True, description='email and key'),
                                         'password': fields.String(required=True,  description='User password', help="password cannot be empty.")})


@register.route('/')
class Reg(Resource):
    @register.doc('reg_user')
    # @register.marshal_list_with(register_model)
    @register.expect(register_model)
    def post(self):
        '''Signup user'''
        body = request.json
        email = body['email']
        password = body['password']
        confirmation = body['confirmation']
        if not User.validEmail(email):
            return {'success': False, 'message': 'incorrect email:  ' + email}, 409

        hasUser = database.selectUser(email)
        if len(hasUser) > 0:
            return {'success': False, 'message': 'User with email ' + email + ' already exists'}, 409
        if password != confirmation:
            return {'success': False, 'message': "Password and confirmation doesn't match"}, 409

        body = User.hash_password(body)
        result = database.insert('users', body)
        return {'success': True, 'message': 'User created ', 'User id': result['_key']}, 200


@users_list.route('/list')
class List(Resource):
    @users_list.doc('reg_list')
    @users_list.expect(users_get_model)
    def post(self):
        data = request.json
        users = database.select('users', " FILTER doc.email == @value ", data['email'])
        if len(users) == 0:
            return {'success': False, 'message': 'user with this email address not found ', 'Email': data['email']}, 200
        else:
            user = users[0]
            User.cleanField(user)
            return {'success': True, 'User': user}, 200


@login.route('/')
class loginApi(Resource):
    @login.doc('login user')
    @login.expect(login_model)
    def post(self):
        body = request.get_json()
        users = database.selectUser(body['email'])
        if len(users) == 0:
            return {'success': False, 'message': 'user with this email address not found ', 'Email': body['email']}, 200
        else:
            user = users[0]
        authorized = User.check_password(user, body['password'])
        expires = datetime.timedelta(days=7)
        access_token = create_access_token(identity=str(user['_id']), expires_delta=expires)
        if authorized:
            User.cleanField(user)
            return {'success': True, 'User': user, 'token': access_token}, 200
        else:
            return {'success': False, 'message': 'Unable to login user'}, 401
