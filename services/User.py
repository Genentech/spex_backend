from database import database
from models.User import user

collection = 'users'


def select_user(email='', id=None):
    value = email
    search = 'FILTER doc.email = @value LIMIT 1'
    if id:
        value = id
        search = 'FILTER doc._id = @value LIMIT 1'

    items = database.select(collection, search, **{'value': value})
    return user(items[0]) if not items[0] is None else None


def select_users():
    items = database.select(collection)
    return [user(items[0]) for item in items]


def insert(data):
    item = database.insert(collection, data)
    return user(item)
