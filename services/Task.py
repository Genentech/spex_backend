from spex_common.modules.database import db_instance
from spex_common.models.Task import task, Task
from services.Utils import first_or_none, map_or_none


_collectionName = 'tasks'


def select(_id, collection=_collectionName) -> Task:
    search = 'FILTER doc._key == @value LIMIT 1'
    items = db_instance().select(collection, search, value=_id)
    return first_or_none(items, task)


def select_tasks(condition=None, collection=_collectionName, **kwargs) -> list[Task]:
    search = db_instance().get_search(**kwargs)
    if condition is not None and search:
        search = search.replace('==',  condition)
    items = db_instance().select(collection, search, **kwargs)
    return map_or_none(items, lambda item: task(item).to_json())


def select_tasks_edge(_key) -> list[Task]:
    items = db_instance().select_edge(collection='jobs_tasks', inbound=False, _key=_key)

    if len(items) < 1:
        return []

    items = list(filter(None.__ne__, items))

    if len(items) < 1:
        return []

    return map_or_none(items, lambda item: task(item).to_json())


def update(_id, data=None, collection='tasks') -> Task:
    search = 'FILTER doc._key == @value LIMIT 1 '
    items = db_instance().update(collection, data, search, value=_id)
    return first_or_none(items, task)


def delete(_id) -> Task:
    search = 'FILTER doc._key == @value LIMIT 1 '
    items = db_instance().delete(_collectionName, search, value=_id)
    return first_or_none(items, task)


def insert(data) -> Task:
    item = db_instance().insert(_collectionName, data)
    return task(item['new']) if item['new'] is not None else None


def count() -> int:
    arr = db_instance().count(_collectionName, '')
    return int(arr[0])


def create_tasks(body, job) -> list[Task]:
    parent = job.id
    result = []

    for omeroId in body['omeroIds']:
        arg = dict()
        arg['name'] = body['name']
        arg['content'] = body['content']
        arg['params'] = body['params']
        arg['omeroId'] = omeroId

        tasks = select_tasks(**arg)

        if tasks is None:
            tasks = []

        if len(tasks) > 0:
            result.append(tasks[0])
        else:
            data = dict(body)
            data['omeroId'] = omeroId
            data['parent'] = parent
            data['status'] = 0
            del data['omeroIds']

            new_task = insert(data)
            if new_task is not None:
                result.append(new_task.to_json())

    for item in result:
        db_instance().insert_edge('jobs_tasks', _from=job._id, _to=item.get('_id'))

    return result
