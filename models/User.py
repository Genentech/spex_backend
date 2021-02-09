from email_validator import validate_email, EmailNotValidError
from flask_bcrypt import generate_password_hash, check_password_hash


class User:
    def __init__(self, **kwargs):
        self.id = kwargs.get('_key', None)
        self.firstName = kwargs.get('firstName', '')
        self.lastName = kwargs.get('lastName', '')
        self.email = kwargs.get('email', '')
        self.password = kwargs.get('password', '')
        self.admin = kwargs.get('admin', False)

    def to_json(self):
        return {
            'id': self.id,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'email': self.email,
            'admin': self.admin
        }

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def hash_password(data):
        data['password'] = generate_password_hash(data['password']).decode('utf8')
        return data

    @staticmethod
    def valid_email(email):
        try:
            # Validate.
            validate_email(email)
            # Update with the normalized form.
            # email = valid.email
            return True
        except EmailNotValidError:
            # email is not valid, exception message is human-readable
            return False


def user(data):
    return User(**data)
