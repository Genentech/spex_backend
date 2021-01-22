from flask_restx import Namespace, Resource, fields
from flask import request
from database import database
from flask_bcrypt import generate_password_hash, check_password_hash

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


class User():

    def hash_password(Data):
        Data['password'] = generate_password_hash(Data['password']).decode('utf8')
        return Data

    def check_password(Data, password):
        return check_password_hash(Data.password, password)


@register.route('/')
class Reg(Resource):
    @register.doc('reg_user')
    # @register.marshal_list_with(register_model)
    @register.expect(register_model)
    def post(self):
        '''Signup user'''
        body = request.json
        hasUser = database.selectUser(body['email'])
        if len(hasUser) > 0:
            #  return res.boom.conflict('Exists', { success: false, message: `User with email ${email} already exists` });
            return 'mustaches'
        body = User.hash_password(body)
        result = database.insert('users', body)
        return result
        # return request.get_json()


@users_list.route('/list')
class List(Resource):
    @users_list.doc('reg_list')
    @users_list.expect(users_get_model)
    def post(self):
        data = request.json
        return database.select('users', " FILTER doc.email == @value ", data['email'])


@login.route('/')
class loginApi(Resource):
    @login.doc('login user')
    @login.expect(login_model)
    def post(self):
        body = request.get_json()
        User = database.selectUser(body['email'])
        # authorized = User.check_password(body.get('password'))
        # body = User.hash_password(body)
        print(User)
        return body, 200
