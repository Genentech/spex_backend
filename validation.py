from email_validator import validate_email, EmailNotValidError
from flask_bcrypt import generate_password_hash, check_password_hash


class User():
    def hash_password(Data):
        Data['password'] = generate_password_hash(Data['password']).decode('utf8')
        return Data

    def check_password(Data, password):
        return check_password_hash(Data['password'], password)

    def validEmail(email):
        try:
            # Validate.
            validate_email(email)
            # Update with the normalized form.
            # email = valid.email
            return True
        except EmailNotValidError:
            # email is not valid, exception message is human-readable
            return False

    def cleanField(data):
        try:
            delField(data, 'password')
            delField(data, 'confirmation')
            return data
        except Exception:
            for element in data:
                delField(element, 'password')
                delField(element, 'confirmation')
            return data


def delField(element, field):
    delP = False
    for key in element.copy():
        if key == field:
            delP = True
    if delP:
        del element[field]
