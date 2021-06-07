from flask_restx import fields, Model
# from .responses import response

file_model = Model('FileBase', {
    'name': fields.String,
    'description': fields.String,
    'parent': fields.String
})

file_get_model = file_model.inherit('File get', {
    'id': fields.String(
        required=True,
        description='Task id'
    )
})
