from arango import ArangoClient
from flask import jsonify
client = ArangoClient(hosts='http://localhost:8529')
db = client.db('genentechdb', username='root', password='pass')


def Initialize_database(db=db):
    sys_db = client.db('_system', username='root', password='pass')
    if not sys_db.has_database('genentechdb'):
        sys_db.create_database('genentechdb')
    db = client.db('genentechdb', username='root', password='pass')
    if not db.has_collection('users'):
        db.create_collection('users', edge=True)
    if not db.has_collection('groups'):
        db.create_collection('groups', edge=True)


def insert(collection, data):
    return db.insert_document(collection, data, True)


def select(collection, filter, value):
    print('FOR doc IN ' + collection + ' ' + filter + ' RETURN doc ')
    cursor = db.aql.execute('FOR doc IN ' + collection + ' ' + filter + ' RETURN doc ', bind_vars={'value': value})
    emails = [doc for doc in cursor]
    return jsonify(emails)
