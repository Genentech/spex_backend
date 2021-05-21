from modules.database import database
from models.Task import task


collection = 'tasks'


def select(id, collection='tasks'):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1'
    items = database.select(collection, search, value=value)
    if len(items) == 0:
        return None
    return task(items[0]) if not items[0] is None else None


def select_tasks(condition=None, collection='tasks', **kwargs):

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
    return [task(item).to_json() for item in items]


def select_tasks_edge(_key):
    items = database.select_edge(collection='jobs-tasks', inboud=False, _key=_key)
    if len(items) == 0:
        return []
    for x in items:
        if x is None:
            items.remove(x)

    return [task(item).to_json() for item in items]


def update(id, data=None, collection='tasks'):
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
        if tasks is None:
            tasks = []
        if len(tasks) > 0:
            arrRes.append(tasks[0])
        else:
            data = dict(body)
            data['omeroId'] = omeroId
            data['parent'] = parent
            data['status'] = 0
            del data['omeroIds']
            newTask = database.insert(collection, data)
            arrRes.append(task(newTask['new']).to_json())
    for item in arrRes:
        database.insert_edge('jobs-tasks', _from=job._id, _to=item.get('_id'))

    return arrRes
