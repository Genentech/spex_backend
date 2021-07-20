from spex_common.modules.database import db_instance
from spex_common.models.Image import image
from services.Utils import first_or_none, map_or_none


collection = 'images'


def select(id):
    value = id
    search = 'FILTER doc.omeroId == @value LIMIT 1'
    items = db_instance().select(collection, search, value=value)
    return first_or_none(items, image)


def select_images(condition=None, collection='images', **kwargs):
    search = db_instance().get_search(**kwargs)
    if condition is not None and search:
        search = search.replace('==',  condition)
    items = db_instance().select(collection, search, **kwargs)
    return map_or_none(items, lambda item: image(item).to_json())


def update(id, data=None):
    search = 'FILTER doc.omeroId == @value LIMIT 1'
    items = db_instance().update(collection, data, search, value=id)
    return first_or_none(items, image)


def delete(id):
    search = 'FILTER doc.omeroId == @value'
    items = db_instance().delete(collection, search, value=id)
    return first_or_none(items, image)


def insert(data):
    item = db_instance().insert(collection, data)
    return image(item['new']) if item['new'] is not None else None


def count():
    arr = db_instance().count(collection, '')
    return arr[0]
