import docker
import os
client = docker.from_env()

envfordocker = {
    'FLASK_ENV': 'production',
    'FLASK_DEBUG': True,
    'SERVER_NAME': 'host.docker.internal:8080',
    'RESTX_ERROR_404_HELP': False,
    'ERROR_404_HELP': False,
    'CORS_HEADERS': 'Content-Type',
    'CORS_METHODS': 'GET,POST,OPTIONS',
    'DATA_STORAGE': '//DATA_STORAGE',
    'SCRIPT_PATH': '//DATA_STORAGE/script.py'
}


def listContainers():
    service = Image()
    if service is None:
        return None
    return client.containers.list(all=True, filters={'ancestor': service.id})


def Image():
    images = client.images.list(filters={'reference': os.getenv('DOCKER_IMAGE')})
    service = images[0] if len(images) > 0 else None
    return service


def mountAndStartContainer(author, path):
    service = Image()
    if service is None:
        return None
    container = client.containers.run(
                                      os.getenv('DOCKER_IMAGE'),
                                      network_mode='host',
                                      volumes={path: {'bind': '/DATA_STORAGE', 'mode': 'rw'}},
                                      labels=author,
                                      detach=True,
                                      name=author.get('id'),
                                      environment=envfordocker,
                                      auto_remove=True
                                      )
    return container
