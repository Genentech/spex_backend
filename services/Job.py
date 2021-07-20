from spex_common.modules.database import db_instance
from spex_common.models.Job import job
from spex_common.models.Connection import connection
from services.Utils import first_or_none, map_or_none


collection = 'jobs'


def select(id, collection='jobs'):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1'
    items = db_instance().select(collection, search, value=value)
    return first_or_none(items, job)


def select_jobs(collection='jobs', condition=None, **kwargs):
    search = db_instance().get_search(**kwargs)
    if condition is not None and search:
        search = search.replace('==',  condition)

    items = db_instance().select(collection, search, **kwargs)
    return map_or_none(items, lambda item: job(item).to_json())


def update(id, collection='jobs', data=None):
    search = 'FILTER doc._key == @value LIMIT 1 '
    items = db_instance().update(collection, data, search, value=id)
    return first_or_none(items, job)


def delete(id, collection='jobs'):
    search = 'FILTER doc._key == @value LIMIT 1 '
    items = db_instance().delete(collection, search, value=id)
    return first_or_none(items, job)


def delete_connection(condition=None, collection='jobs_tasks', **kwargs):
    search = db_instance().get_search(**kwargs)
    if condition is not None and search:
        search = search.replace('==',  condition)
    items = db_instance().delete(collection, search, **kwargs)
    return first_or_none(items, job)


def select_connections(condition=None, collection="jobs_tasks", one=False, **kwargs):
    search = db_instance().get_search(**kwargs)
    if condition is not None and search:
        search = search.replace('==',  condition)

    items = db_instance().select(collection, search, **kwargs)

    def to_json(item):
        connection(item).to_json()

    if one:
        return first_or_none(items, to_json)

    return map_or_none(items, to_json)


def insert(data, collection='jobs'):
    item = db_instance().insert(collection, data)
    return job(item['new']) if item['new'] is not None else None


def count(collection='jobs'):
    arr = db_instance().count(collection, '')
    return arr[0]
