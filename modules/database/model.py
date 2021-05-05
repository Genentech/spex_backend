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
            collection = db.create_collection('users')
            collection.add_hash_index(fields=["username"], unique=True)
        if not db.has_collection('images'):
            db.create_collection('images')
        if not db.has_collection('groups'):
            db.create_collection('groups')
        if not db.has_collection('jobs'):
            db.create_collection('jobs')
        if not db.has_collection('tasks'):
            db.create_collection('tasks')
        if not db.has_collection('projects'):
            db.create_collection('projects')
        if not db.has_collection('jobs-tasks'):
            db.create_collection('jobs-tasks', edge=True)
        if not db.has_collection('task-result'):
            db.create_collection('task-result')
        if not db.has_collection('pipeline'):
            db.create_collection('pipeline', edge=True)

    def insert(self, collection, data, overwrite_mode=None):
        return self.instance.insert_document(collection, data, True, overwrite_mode=overwrite_mode)

    def select(self, collection, search='', fields='doc', **kwargs):
        task = self.async_instance.aql.execute(
            f'FOR doc IN {collection} {search} RETURN {fields}',
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
            f'FOR doc IN  {collection} '
            f'{search} '
            f' REMOVE doc IN {collection} '
            f' LET deleted = OLD '
            f' RETURN UNSET(deleted, "_key", "_id", "_rev", "password") ',
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

    def insert_edge(self, collection, _from='', _to=''):

        request_text = f'insert (_from: "{_from}", _to: "{_to}") into "{collection}"'.replace("(", "{").replace(")", "}")
        data = self.async_instance.aql.execute(request_text)
        return receive_async_response(data)

    def select_edge(self, collection, inboud, _key):
        if inboud is True:
            inboud = 'inbound'
        else:
            inboud = 'outbound'

        request_text = f'for doc in {inboud} "{_key}" @collection return doc '
        data = self.async_instance.aql.execute(request_text, bind_vars={'collection': collection})
        return receive_async_response(data)

    def get_search(self, **kwargs):
        search = 'FILTER '
        count = 0
        for key, value in kwargs.items():
            count = count + 1
            search = search + 'doc.' + key + ' == @' + key
            if count != len(kwargs.items()):
                search = search + " && "
        return search
