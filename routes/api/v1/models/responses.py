from flask_restx import fields, Model

response = Model('Response', {
    'success': fields.Boolean(
        required=True,
        description='Status of operation',
    ),
})

error_response = response.inherit('Error', {
    'message': fields.String(
        required=True,
        description='Reason of error',
    )
})
