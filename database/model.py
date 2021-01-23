from arango import ArangoClient
from arango.database import StandardDatabase, AsyncDatabase
# from arango.collection import StandardCollection
from arango.job import AsyncJob
import ujson
import time


client = ArangoClient(hosts='http://localhost:8529')
db = client.db('genentechdb', username='root', password='pass')


class ArangoDB():
    client: ArangoClient
    instance: StandardDatabase
    async_instance: AsyncDatabase
    tasks: dict

    def __init__(
        self,
        hosts: str = "0.0.0.0:8529",
        database: str = "genentechdb",
        username: str = "",
        password: str = "",
    ):
        self.client = ArangoClient(
            hosts=hosts,
            serializer=ujson.dumps,
            deserializer=ujson.loads,
        )
        self.instance = self.client.db(database, username=username, password=password)
        self.async_instance = self.instance.begin_async_execution(return_result=True)

    def receive_asynс_response(self, task: AsyncJob):
        while task.status() != 'done':
            time.sleep(0.1)
        return [i for i in task.result()]

    def Initialize(self, db=db):
        sys_db = self.client.db('_system', username='root', password='pass')
        if not sys_db.has_database('genentechdb'):
            sys_db.create_database('genentechdb')
        db = self.instance
        if not db.has_collection('users'):
            db.create_collection('users', edge=True)
        if not db.has_collection('groups'):
            db.create_collection('groups', edge=True)

    def insert(self, collection, data):
        return db.insert_document(collection, data, True)

    def select(self, collection, filter, value):
        task = self.async_instance.aql.execute('FOR doc IN ' + collection + ' ' + filter + ' RETURN doc ', bind_vars={'value': value})
        emails = self.receive_asynс_response(task)
        return emails

    def selectUser(self, value):
        task = self.async_instance.aql.execute('FOR doc IN users FILTER doc.email == @value LIMIT 1 RETURN  doc ',
                                               bind_vars={'value': value}, count=True)
        users = self.receive_asynс_response(task)
        return users
