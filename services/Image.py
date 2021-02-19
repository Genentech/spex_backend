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


def select_images():
    items = database.select(collection)
    if len(items) == 0:
        return None
    return [image(items[0]) for item in items]


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
