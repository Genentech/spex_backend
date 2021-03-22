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
        self.username = username
        self.password = password
        self.database = database

    def initialize(self):
        sys_db = self.client.db(
            '_system',
            username=self.username,
            password=self.password
        )

        if not sys_db.has_database(self.database):
            sys_db.create_database(self.database)

        self.instance = self.client.db(
            self.database,
            self.username,
            self.password
        )
        self.password = None
        self.async_instance = self.instance.begin_async_execution(return_result=True)

        db = self.instance

        if not db.has_collection('users'):
            db.create_collection('users')
        if not db.has_collection('images'):
            db.create_collection('images')
        if not db.has_collection('groups'):
            db.create_collection('groups')
        if not db.has_collection('jobs'):
            db.create_collection('jobs')
        if not db.has_collection('tasks'):
            db.create_collection('tasks')

    def insert(self, collection, data):
        return self.instance.insert_document(collection, data, True)

    def select(self, collection, search='', **kwargs):
        task = self.async_instance.aql.execute(
            f'FOR doc IN {collection} {search} RETURN doc',
            bind_vars={
                **kwargs
            }
        )
        return receive_async_response(task)

    def update(self, collection, data, search='', **kwargs):
        task = self.async_instance.aql.execute(
            f'FOR doc IN {collection} {search}'
            f' UPDATE doc WITH {data} IN {collection}'
            f' LET updated = NEW'
            f' Return UNSET(updated, "_key", "_id", "_rev", "password")',
            bind_vars={
                **kwargs
            }
        )
        return receive_async_response(task)

    def delete(self, collection, search='', **kwargs):
        task = self.async_instance.aql.execute(
            f'FOR doc IN  {collection} {collection}'
            f' REMOVE doc IN {search}'
            f' LET deleted = OLD'
            f' RETURN UNSET(deleted, "_key", "_id", "_rev", "password")',
            bind_vars={
                **kwargs
            }
        )
        return receive_async_response(task)

    def count(self, collection, search='', **kwargs):
        task = self.async_instance.aql.execute(
            f'FOR doc IN {collection} {search} COLLECT WITH COUNT INTO length RETURN length',
            bind_vars={
                **kwargs
            }
        )
        return receive_async_response(task)
