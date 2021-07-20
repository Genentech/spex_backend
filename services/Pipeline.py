from spex_common.modules.database import db_instance
from spex_common.models.Pipeline import pipeline
from services.Utils import first_or_none, map_or_none

collectionName = 'pipeline_direction'


def select(id, collection=collectionName, to_json=False):
    search = 'FILTER doc._key == @value LIMIT 1'
    items = db_instance().select(collection, search, value=id)
    return map_or_none(items, lambda item: (pipeline(item).to_json() if to_json else pipeline(item)))


def select_pipeline(condition=None, collection=collectionName, one=False, **kwargs):
    search = db_instance().get_search(**kwargs)
    if condition is not None and search:
        search = search.replace('==',  condition)

    items = db_instance().select(collection, search, **kwargs)

    def to_json(item):
        pipeline(item).to_json()

    if one:
        return first_or_none(items, to_json)

    return map_or_none(items, to_json)


def select_pipeline_edge(_key):
    items = db_instance().select_edge(collection=collectionName, inboud=False, _key=_key)

    def to_json(item):
        pipeline(item).to_json()

    if len(items) == 1:
        return first_or_none(items, to_json)

    return map_or_none(items, to_json)


def update(id, data=None, collection=collectionName):
    search = 'FILTER doc._key == @value LIMIT 1 '
    items = db_instance().update(collection, data, search, value=id)
    return first_or_none(items, pipeline)


def delete(condition=None, collection=collectionName, **kwargs):
    search = db_instance().get_search(**kwargs)
    if condition is not None and search:
        search = search.replace('==',  condition)
    items = db_instance().delete(collection, search, **kwargs)
    return first_or_none(items, pipeline)


def insert(data, collection=collectionName):
    item = db_instance().insert(collection, data)
    return pipeline(item['new']) if item['new'] is not None else None


def count():
    arr = db_instance().count(collectionName, '')
    return arr[0]


def createPipeline(body, job):
    arrRes = []
    return arrRes
