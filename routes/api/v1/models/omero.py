from flask_restx import fields, Model
from .responses import response

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

omero_tree_response = response.inherit('json tree', {
    'data': {}
})
