from flask_restx import fields, Model
from .responses import response

user_model = Model('UserBase', {
    'username': fields.String(
        required=True,
        description='Username'
    ),
    'omeroUserId': fields.String(
        required=True,
        description='User Id in Omero'
    ),
    'email': fields.String(
        description='User email'
    ),
    'firstName': fields.String(
        description='Firstname',
    ),
    'lastName': fields.String(
        description='Lastname',
    )
})

user_get_model = user_model.inherit('User', {
    'id': fields.String(
        required=True,
        description='User id'
    )
})

login_model = Model('UserLogin', {
    'username': fields.String(
        required=True,
        description='Email'
    ),
    'password': fields.String(
        required=True,
        description='User password',
        help='password cannot be empty.'
    )
})

a_user_response = response.inherit('UserResponse', {
    'data': fields.Nested(user_get_model)
})

list_user_response = response.inherit('UsersListResponse', {
    'data': fields.List(fields.Nested(user_get_model))
})
