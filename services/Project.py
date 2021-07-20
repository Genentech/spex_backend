from spex_common.modules.database import db_instance
from spex_common.models.Project import project
from services.Utils import first_or_none, map_or_none


collection = 'projects'


def select(id):
    search = 'FILTER doc._key == @value LIMIT 1'
    items = db_instance().select(collection, search, value=id)
    return first_or_none(items, project)


def select_projects(**kwargs):
    search = db_instance().get_search(**kwargs)
    items = db_instance().select(collection, search, **kwargs)
    return map_or_none(items, lambda item: project(item).to_json())


def update(id, data=None):
    search = 'FILTER doc._key == @value LIMIT 1 '
    items = db_instance().update(collection, data, search, value=id)
    return first_or_none(items, project)


def delete(**kwargs):
    search = db_instance().get_search(**kwargs)
    items = db_instance().delete(collection, search, **kwargs)
    return first_or_none(items, project)


def insert(data):
    item = db_instance().insert(collection, data)
    return project(item['new']) if item['new'] is not None else None


def count():
    arr = db_instance().count(collection, '')
    return arr[0]
