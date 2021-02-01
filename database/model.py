import time
import ujson
from arango import ArangoClient
from arango.database import StandardDatabase, AsyncDatabase
from arango.job import AsyncJob


def receive_async_response(task: AsyncJob):
    while task.status() != 'done':
        time.sleep(0.1)
    return [i for i in task.result()]


class ArangoDB:
    client: ArangoClient
    instance: StandardDatabase
    async_instance: AsyncDatabase

    def __init__(
        self,
        hosts: str = '0.0.0.0:8529',
        database: str = 'genentechdb',
        username: str = '',
        password: str = '',
    ):
        self.client = ArangoClient(
            hosts,
            serializer=ujson.dumps,
            deserializer=ujson.loads,
        )
        self.instance = self.client.db(database, username, password)
        self.async_instance = self.instance.begin_async_execution(return_result=True)

    def initialize(self):
        sys_db = self.client.db('_system', username='root', password='pass')

        if not sys_db.has_database('genentechdb'):
            sys_db.create_database('genentechdb')

        db = self.instance

        if not db.has_collection('users'):
            db.create_collection('users', edge=True)

        if not db.has_collection('groups'):
            db.create_collection('groups', edge=True)

    def insert(self, collection, data):
        return self.instance.insert_document(collection, data, True)

    def select(self, collection, search='', **kwargs):
        task = self.async_instance.aql.execute(
            'FOR doc IN {} {} RETURN doc'.format(collection, search),
            bind_vars={
                **kwargs
            }
        )
        return receive_async_response(task)

    # TODO delete and update
