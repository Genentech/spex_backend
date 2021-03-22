from datetime import datetime
from urllib import parse
from requests import Session
from os import getenv
from services.Cache import CacheService


__all__ = ['get', 'get_or_create', 'OmeroSession']


class OmeroSession(Session):
    def __init__(self, session_id=None, token=None, context=None):
        super().__init__()
        self.__attrs__.extend([
            'omero_session_id',
            'omero_token',
            'omero_context'
        ])
        self.omero_session_id = session_id
        self.omero_token = token
        self.omero_context = context

        if session_id:
            self.cookies.setdefault('sessionid', session_id)

        if token:
            self.headers.setdefault('X-CSRFToken', token)

    def request(self, method: str, url: str, **kwargs):
        result = parse.urlparse(url)

        if not result.netloc or not result.scheme:
            url = parse.urljoin(getenv("OMERO_PROXY_PATH"), url)

        return super(OmeroSession, self).request(
            method,
            url,
            **kwargs
        )


def _login_omero_web(login, password, server='1'):
    client = OmeroSession()

    response = client.get('/api/v0/token/')

    data = response.json()

    csrf_token = data['data']

    data = {
        'username': login,
        'password': password,
        'server': server
    }

    url = '/api/v0/login/'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrf_token
    }
    response = client.post(url, headers=headers, data=data)

    data = response.json()

    if response.status_code == 200 and data['success']:
        session = OmeroSession(
            response.cookies['sessionid'],
            csrf_token,
            data['eventContext']
        )

        CacheService.set(login, session)
    else:
        CacheService.delete(login)

    return get(login)


def get(login):
    session = CacheService.get(login)

    if not session:
        return None

    timestamp = int(datetime.timestamp(datetime.now()) * 1000)

    url = f'/webclient/keepalive_ping/?_={timestamp}'
    response = session.get(url)

    if response.status_code == 200:
        return session

    CacheService.delete(login)

    return None


def get_or_create(login, password):
    session = get(login)

    if not session:
        session = _login_omero_web(login, password)

    return session

