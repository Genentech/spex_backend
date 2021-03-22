class User:
    def __init__(self, **kwargs):
        self.id = kwargs.get('_key', None)
        self.firstName = kwargs.get('firstName', '')
        self.lastName = kwargs.get('lastName', '')
        self.omeroUserId = kwargs.get('omeroUserId', '')
        self.email = kwargs.get('email', '')
        self.admin = kwargs.get('admin', False)
        self.username = kwargs.get('username', '')

    def to_json(self):
        return {
            'id': self.id,
            'omeroUserId': self.omeroUserId,
            'username': self.username,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'email': self.email,
            'admin': self.admin
        }


def user(data):
    return User(**data)
