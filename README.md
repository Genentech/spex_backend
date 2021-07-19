# spex/backend



## Getting Started

Download links:

SSH clone URL: git@ssh.code.roche.com:spex/backend.git

HTTPS clone URL: https://code.roche.com/spex/backend.git



These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

## Production

copy `.env` to `.env.local` and specify correct values for variables  
`$ docker compose up -d --build`  


copy `.env.common` to `.env.common.local` and specify correct values for variables  
`$ docker compose -f ./micro-service/docker-compose.yml --project-directory ./micro-service up -d --build`

## Deployment

1. Memcached

`$ docker run --name spex_memcached -p 11211:11211 -d memcached memcached -m 64`

2. Redis

```
$ cd ./micro-services/redis  
$ docker build --pull --rm -t spex_redisjson .
$ docker run -p 6379:6379 --name spex_redisjson -d spex_redisjson
$ cd ../..
```

3. ArangoDB

`$ docker run -p 8529:8529 -e ARANGO_ROOT_PASSWORD=pass --name spex_arangodb -d arangodb:3.7.7`

will set user/password
```
user: root
pass: pass
```

4. Copy `.env.development` to `.env.development.local`

5. Set the following variables:
```
ARANGODB_DATABASE_URL=http://localhost:8529

REDIS_HOST=localhost
REDIS_PORT=6379

MEMCACHED_HOST=127.0.0.1:11211

DATA_STORAGE=${TEMP}\\DATA_STORAGE
```

6. Run server
```
$ pip install pipenv 
$ pipenv install --system --deploy --ignore-pipfile
$ pipenv shell
$ export MODE=development
$ python ./app.py
```

## Resources

Add links to external resources for this project, such as CI server, bug tracker, etc.
