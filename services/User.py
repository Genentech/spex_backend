from spex_common.modules.database import db_instance
from spex_common.models.User import user, User
from services.Utils import first_or_none, map_or_none

collection = 'users'


def select(username='', id=None) -> User:
    value = username
    search = 'FILTER doc.username == @value LIMIT 1'
    if id:
        value = id
        search = 'FILTER doc._key == @value LIMIT 1'

    items = db_instance().select(collection, search, value=value)
    return first_or_none(items, user)


def select_users() -> list[User]:
    items = db_instance().select(collection)
    return map_or_none(items, user)


def update(username='', id=None, data=None) -> User:
    value = username
    search = 'FILTER doc.username == @value LIMIT 1'
    if id:
        value = id
        search = 'FILTER doc._key == @value LIMIT 1'

    items = db_instance().update(collection, data, search, value=value)
    return first_or_none(items, user)


def delete(username='', id=None) -> User:
    value = username
    search = 'FILTER doc.username == @value '
    if id:
        value = id
        search = 'FILTER doc._key == @value '

    items = db_instance().delete(collection, search, value=value)
    return first_or_none(items, user)


def insert(data) -> User:
    item = db_instance().insert(collection, data)
    return user(item['new']) if item['new'] is not None else None


def count() -> int:
    arr = db_instance().count(collection, '')
    return int(arr[0])


def is_admin(id) -> bool:
    item = select(id=id)

    return item.admin if item is not None else False
