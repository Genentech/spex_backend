from flask_restx import Namespace, Resource, fields
from flask import request
from database.db import insert, select

register = Namespace('register', description='User registration')
users_list = Namespace('user list', description='User list')
users_get_model = users_list.model('user list', {'email': fields.String(required=True, description='email and key')})


register_model = register.model('register', {
    'email': fields.String(required=True, description='email and key'),
    'password': fields.String(required=True,  description='User password', help="password cannot be empty."),
    'firstName': fields.String(required=True,  description='Firstname', help="First name cannot be empty."),
    'lastName': fields.String(required=True,  description='Lastname', help="Lastname cannot be empty."),
    'confirmation': fields.String(required=True,  description='Confirmation', help="Confirmation password cannot be empty.")
})


@register.route('/')
class Reg(Resource):
    @register.doc('reg_user')
    # @register.marshal_list_with(register_model)
    @register.expect(register_model)
    def post(self):
        '''Fetch a users given its identifier'''
        data = request.json
        result = insert('users', data)
        return result
        # return request.get_json()


@users_list.route('/list')
class List(Resource):
    @users_list.doc('reg_list')
    @users_list.expect(users_get_model)
    def post(self):
        data = request.json
        return select('users', " FILTER doc.email == @value ", data['email'])
