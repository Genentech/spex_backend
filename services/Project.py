from modules.database import database
from models.Project import project


collection = 'projects'


def select(id, **kwargs):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1'
    items = database.select(collection, search, value=value)
    if len(items) == 0:
        return None
    return project(items[0]) if not items[0] is None else None


def select_projects(**kwargs):
    search = database.get_search(**kwargs)
    items = database.select(collection, search, **kwargs)
    if len(items) == 0:
        return None
    return [project(item).to_json() for item in items]


def update(id, data=None):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1 '

    items = database.update(collection, data, search, value=value)
    if len(items) == 0:
        return None
    return project(items[0]) if not items[0] is None else None


def delete(**kwargs):
    search = database.get_search(**kwargs)
    items = database.delete(collection, search, **kwargs)
    if len(items) == 0:
        return None
    return project(items[0]) if not items[0] is None else None


def insert(data):
    item = database.insert(collection, data)
    return project(item['new'])


def count():
    arr = database.count(collection, '')
    return arr[0]
