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


def list_containers(author=None, name='', **kwargs):
    service = image()
    if service is None:
        return None
    filters = {'ancestor': service.id}
    if author is not None:
        filters.update({'label': [f'id={author.get("id")}', f'login={author.get("login")}']})
    if name is not None:
        filters.update({'name': name})
    if kwargs is not None:
        filters.update(kwargs)
    return client.containers.list(all=True, filters=filters)


def prune_containers(**kwargs):
    service = image()
    filters = {}
    if service is None:
        return None
    if kwargs is not None:
        filters.update(kwargs)
    return client.containers.prune(filters=filters)


def image():
    images = client.images.list(filters={'reference': os.getenv('DOCKER_IMAGE')})
    service = images[0] if len(images) > 0 else None
    return service


def mount_and_start_container(author, path, name='', auto_remove=False):
    service = image()
    string = ''
    if name != '':
        string = '-'
    if service is None:
        return None
    container = client.containers.run(
                                      os.getenv('DOCKER_IMAGE'),
                                      network_mode='host',
                                      volumes={path: {'bind': '/DATA_STORAGE', 'mode': 'rw'}},
                                      labels=author,
                                      detach=True,
                                      name=author.get('id') + string+''.join(filter(str.isalnum, name)),
                                      environment=envfordocker,
                                      auto_remove=auto_remove
                                      )
    return container
