from database.db import ArangoDB
from config import ARANGODB_DATABASE_URL, ARANGODB_DATABASE_NAME

database: ArangoDB = ArangoDB(
    hosts=ARANGODB_DATABASE_URL, database=ARANGODB_DATABASE_NAME
)
