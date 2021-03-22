from os import getenv
from modules.database.model import ArangoDB

database = ArangoDB(
    getenv('ARANGODB_DATABASE_URL', 'http://0.0.0.0:8529'),
    getenv('ARANGODB_DATABASE_NAME', 'genentechdb'),
    getenv('ARANGODB_USERNAME'),
    getenv('ARANGODB_PASSWORD')
)
