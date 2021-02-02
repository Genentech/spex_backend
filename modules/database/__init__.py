from os import getenv
from modules.database.model import ArangoDB

database = ArangoDB(
    getenv('ARANGODB_DATABASE_URL'),
    getenv('ARANGODB_DATABASE_NAME'),
    getenv('ARANGODB_USERNAME'),
    getenv('ARANGODB_PASSWORD')
)
