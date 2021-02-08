from flask_restx import fields, Model
from .responses import response

user_model = Model('UserBase', {
    'email': fields.String(
        required=True,
        description='Email'
    ),
    'firstName': fields.String(
        description='Firstname',
    ),
    'lastName': fields.String(
        description='Lastname',
    )
})

signup_model = user_model.inherit('UserSignup', {
    'email': fields.String(
        required=True,
        description='email and key'
    ),
    'password': fields.String(
        required=True,
        description='User password',
        help="password cannot be empty."
    ),
    'confirmation': fields.String(
        required=True,
        description='Confirmation password cannot be empty',
        help='Confirmation password cannot be empty.'
    )
})

user_get_model = user_model.inherit('User', {
    'id': fields.String(
        required=True,
        description='User id'
    )
})

login_model = Model('UserLogin', {
    'email': fields.String(
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
