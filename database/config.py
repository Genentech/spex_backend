from os import getenv, path

DIRECTORY = path.abspath(__file__).rstrip("config.py")
ARANGODB_DATABASE_NAME = getenv("ARANGODB_DATABASE_NAME") or "genentech"
ARANGODB_DATABASE_URL = getenv("ARANGODB_DATABASE_URL") or "http://localhost:8529"
