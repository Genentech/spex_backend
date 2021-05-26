from flask_restx import fields, Model
from .responses import response

paths = Model('PathBase', {'path': fields.String, 'format': fields.String, 'date': fields.Date})

image_model = Model('ImgBase', {
    'name': fields.String,
    'omeroId': fields.String(requred=False),
    'paths': fields.List(fields.Nested(paths))
})

image_get_model = image_model.inherit('ImgGet', {
    'id': fields.String(
        required=True,
        description='image id'
    )
})

task_post_model = image_model.inherit('Task post', {
    'ids': fields.List(fields.String, required=True, description='Task id')
})


list_images_response = response.inherit('ImageListResponse', {
    'data': fields.List(fields.Nested(image_get_model))
})

a_images_response = response.inherit('ImagesResponse', {
    'data': fields.List(fields.Nested(image_get_model))
})
