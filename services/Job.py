from modules.database import database
from models.Job import job
from models.Connection import conn


collection = 'jobs'


def select(id, collection='jobs'):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1'
    items = database.select(collection, search, value=value)
    if len(items) == 0:
        return None
    return job(items[0]) if not items[0] is None else None


def select_jobs(collection='jobs', condition=None, **kwargs):

    search = 'FILTER '
    count = 0
    for key, value in kwargs.items():
        count = count + 1
        search = search + 'doc.' + key + ' == @' + key
        if count != len(kwargs.items()):
            search = search + " && "
    if condition is not None:
        search = search.replace('==',  condition)

    items = database.select(collection, search, **kwargs)
    if len(items) == 0:
        return None
    return [job(item).to_json() for item in items]


def update(id, collection='jobs', data=None):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1 '

    items = database.update(collection, data, search, value=value)
    if len(items) == 0:
        return None
    return job(items[0]) if not items[0] is None else None


def delete(id, collection='jobs'):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1 '
    items = database.delete(collection, search, value=value)
    if len(items) == 0:
        return None
    return job(items[0]) if not items[0] is None else None


def delete_connection(condition=None, collection='jobs_tasks', **kwargs):
    search = 'FILTER '
    count = 0
    for key, value in kwargs.items():
        count = count + 1
        search = search + 'doc.' + key + ' == @' + key
        if count != len(kwargs.items()):
            search = search + " && "
    if condition is not None:
        search = search.replace('==',  condition)
    items = database.delete(collection, search, **kwargs)
    if len(items) == 0:
        return None
    return conn(items[0]) if not items[0] is None else None


def select_connections(condition=None, collection="jobs_tasks", one=False, **kwargs):

    search = 'FILTER '
    count = 0
    for key, value in kwargs.items():
        count = count + 1
        search = search + 'doc.' + key + ' == @' + key
        if count != len(kwargs.items()):
            search = search + " && "
    if condition is not None:
        search = search.replace('==',  condition)

    items = database.select(collection, search, **kwargs)
    if len(items) == 0:
        return None
    if one is True:
        return conn(items[0]).to_json()
    return [conn(item).to_json() for item in items]


def insert(data, collection='jobs'):
    item = database.insert(collection, data)
    return job(item['new'])


def count(collection='jobs'):
    arr = database.count(collection, '')
    return arr[0]
