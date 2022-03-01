# spex/backend



## Getting Started

Download links:

SSH clone URL: git@ssh.code.roche.com:spex/backend.git

HTTPS clone URL: https://code.roche.com/spex/backend.git



These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

## Production

1. Make symbolic links in of all microservices from `../microservices` to `./microservices`  
2. copy `./microservices/.env.common` to `./microservices/.env.common.local` and specify correct values for `OMERO_HOST` and `OMERO_WEB`  
3. copy `.env` to `.env.local` and specify correct values for variables  
4. Set needed path in environment variable HOST_DATA_STORAGE
5. `$ export HOST_DATA_STORAGE=<path> && docker-compose up -d --build`

## Deployment

1. Memcached

`$ docker run --name spex_memcached -p 11211:11211 -d memcached memcached -m 64`

2. Redis

```
$ cd ./microservices/redis  
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
REDIS_SESSION_ALIVE_H=12

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

7. for start all microservices  
8. 
copy `./microservices/.env.common` to `./microservices/.env.common.local` and 
specify correct values for `OMERO_HOST` and `OMERO_WEB`  
`$ docker-compose -f ./microservices/docker-compose.yml --project-directory ./microservices up -d --build`

## Resources

Add links to external resources for this project, such as CI server, bug tracker, etc.
