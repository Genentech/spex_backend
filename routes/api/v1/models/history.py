from flask_restx import fields, Model
from .responses import response

history_model = Model('HistsBase', {
    'content': fields.String,
    'date': fields.DateTime(dt_format='rfc822'),
    'parent': fields.String,
})

history_get_model = history_model.inherit('History get', {
    'id': fields.String(
        required=True,
        description='Hist id'
    ),
    'author': fields.Wildcard(fields.String)
})

history_post_model = history_model.inherit('History post')


list_history_response = response.inherit('HistoryListResponse', {
    'data': fields.List(fields.Nested(history_get_model))
})

a_history_response = response.inherit('TasksResponse', {
    'data': fields.List(fields.Nested(history_get_model))
})
