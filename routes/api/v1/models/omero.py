from flask_restx import fields, Model
# from .responses import response

omero_tree_model = Model('OmeroTree', {
    'login': fields.String(
        required=True,
        description='Omero login'
    ),
    'password': fields.String(
        required=True,
        description='Omero user password',
        help='password cannot be empty.'
    )
})

user_model = Model('UserOmeroBase', {
    'login': fields.String(
        required=True,
        description='login'
    ),
    'password': fields.String(
        description='Password',
    )
})


login_model = Model('UserLoginOmero', {
    'login': fields.String(
        required=True,
        description='Login'
    ),
    'password': fields.String(
        required=True,
        description='User password',
        help='password cannot be empty.'
    )
})

omero_thumbnail = Model('getThumbnail', {
    'login': fields.String(
        required=True,
        description='Omero login'
    ),
    'password': fields.String(
        required=True,
        description='Omero user password',
        help='password cannot be empty.'
    ),
    'imageId': fields.String(
        required=True,
        description='Omero image id',
        help='image id cannot be empty.'
    ),
    'size': fields.Integer(
        required=False,
        description='size im px'
    )
})

omero_download_model = Model('OmeroDownloadImage', {
    'login': fields.String(
        required=True,
        description='Omero login'
    ),
    'password': fields.String(
        required=True,
        description='Omero user password',
        help='password cannot be empty.'
    ),
    'imageId': fields.String(
        required=True,
        description='Omero image id',
        help='image id cannot be empty.'
    )
})


login_responce = Model('omero Login responce', {
    'Authorization': fields.String(
        required=True,
        description='Bearer token'
    )
})
