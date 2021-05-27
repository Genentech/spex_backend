from modules.database import database
from models.Image import image


collection = 'images'


def select(id):
    value = id
    search = 'FILTER doc.omeroId == @value LIMIT 1'
    items = database.select(collection, search, value=value)
    if len(items) == 0:
        return None
    return image(items[0]) if not items[0] is None else None


def select_images(condition=None, collection='images', **kwargs):

    search = 'FILTER '
    count = 0
    for key, value in kwargs.items():
        count = count + 1
        search = search + 'doc.' + key + ' == @' + key
        if count != len(kwargs.items()):
            search = search + " && "
    if condition is not None:
        search = search.replace('==',  condition)
    if search == 'FILTER ':
        search = ''

    items = database.select(collection, search, **kwargs)
    if len(items) == 0:
        return None
    return [image(item).to_json() for item in items]


def update(id, data=None):
    value = id
    search = 'FILTER doc.omeroId == @value LIMIT 1'

    items = database.update(collection, data, search, value=value)
    if len(items) == 0:
        return None
    return image(items[0]) if not items[0] is None else None


def delete(id):
    value = id
    search = 'FILTER doc.omeroId == @value '
    items = database.delete(collection, search, value=value)
    if len(items) == 0:
        return None
    return image(items[0]) if not items[0] is None else None


def insert(data):
    item = database.insert(collection, data)
    return image(item['new'])


def count():
    arr = database.count(collection, '')
    return arr[0]
