from modules.database import database
from models.User import user

collection = 'users'


def select_user(email='', id=None):
    value = email
    search = 'FILTER doc.email == @value LIMIT 1'
    if id:
        value = id
        search = 'FILTER doc._key == @value LIMIT 1'

    items = database.select(collection, search, value=value)
    if len(items) == 0:
        return None
    return user(items[0]) if not items[0] is None else None


def select_users():
    items = database.select(collection)
    if len(items) == 0:
        return None
    return [user(items[0]) for item in items]


def update_user(email='', id=None, data=None):
    value = email
    search = 'FILTER doc.email == @value LIMIT 1'
    if id:
        value = id
        search = 'FILTER doc._key == @value LIMIT 1'

    items = database.update(collection, data, search, value=value)
    if len(items) == 0:
        return None
    return user(items[0]) if not items[0] is None else None


def delete_user(email='', id=None):
    value = email
    search = 'FILTER doc.email == @value '
    if id:
        value = id
        search = 'FILTER doc._key == @value '

    items = database.delete(collection, search, value=value)
    if len(items) == 0:
        return None
    return user(items[0]) if not items[0] is None else None


def insert(data):
    item = database.insert(collection, data)
    return user(item)
