from datetime import datetime, timedelta
from urllib import parse
from requests import Session
from os import getenv
from services.Cache import CacheService


__all__ = ['get', 'create', 'OmeroSession']


class OmeroSession(Session):
    def __init__(self, session_id=None, token=None, context=None, active_until=None):
        super().__init__()
        self.__attrs__.extend([
            'omero_session_id',
            'omero_token',
            'omero_context',
            'active_until'
        ])
        self.omero_session_id = session_id
        self.omero_token = token
        self.omero_context = context
        self.active_until = active_until

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
    client = OmeroSession(active_until=datetime.now() + timedelta(hours=int(getenv('MEMCACHED_SESSION_ALIVE_H'))))

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
            data['eventContext'],
            datetime.now() + timedelta(hours=int(getenv('MEMCACHED_SESSION_ALIVE_H')))
        )

        CacheService.set(login, session)
    else:
        CacheService.delete(login)

    return get(login)


def get(login):
    session = CacheService.get(login)
    if session is not None:
        session.active_until = datetime.now() + timedelta(hours=int(getenv('MEMCACHED_SESSION_ALIVE_H')))
        CacheService.set(login, session)
    if not session:
        return None

    timestamp = int(datetime.timestamp(datetime.now()) * 1000)

    url = f'/webclient/keepalive_ping/?_={timestamp}'
    response = session.get(url)

    if response.status_code == 200:
        return session

    CacheService.delete(login)

    return None


def create(login, password):
    return _login_omero_web(login, password)
