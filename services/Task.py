from modules.database import database
from models.Task import task


collection = 'tasks'


def select(id):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1'
    items = database.select(collection, search, value=value)
    if len(items) == 0:
        return None
    return task(items[0]) if not items[0] is None else None


def select_tasks(**kwargs):

    search = 'FILTER '
    count = 0
    for key, value in kwargs.items():
        # doc.name == @name && doc.content == @content && doc.omeroId == @omeroId
        count = count + 1
        search = search + 'doc.' + key + ' == @' + key
        if count != len(kwargs.items()):
            search = search + " && "

    items = database.select(collection, search, **kwargs)
    if len(items) == 0:
        return None
    return [task(item).to_json() for item in items]


def update(id, data=None):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1 '

    items = database.update(collection, data, search, value=value)
    if len(items) == 0:
        return None
    return task(items[0]) if not items[0] is None else None


def delete(id):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1 '
    items = database.delete(collection, search, value=value)
    if len(items) == 0:
        return None
    return task(items[0]) if not items[0] is None else None


def insert(data):
    item = database.insert(collection, data)
    return task(item['new'])


def count():
    arr = database.count(collection, '')
    return arr[0]


def createTasks(body, job):
    parent = job.id
    arrRes = []

    for omeroId in body['omeroIds']:
        arg = dict()
        arg['name'] = body['name']
        arg['content'] = body['content']
        arg['omeroId'] = omeroId
        tasks = select_tasks(**arg)
        if len(tasks) > 0:
            arrRes.append(tasks[0])
        else:
            data = dict(body)
            data['omeroId'] = omeroId
            data['parent'] = parent
            data['status'] = 0
            del data['omeroIds']
            newTask = database.insert(collection, data)
            arrRes.append(newTask['new'])

    return arrRes
