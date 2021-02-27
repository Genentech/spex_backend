import requests


class Proxy():
    client: None

    def __init__(
        self,
        client,
        username: str = '',
        password: str = '',
    ):
        self.client = client
        self.username = username
        self.password = password

    def createFind(self, username, password):
        if self.client is None:
            self.loginOmeroProxy(username, password)

    def loginOmeroProxy(self, username, password, server='1'):

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        client = requests.session()
        URL = 'http://127.0.0.1:4080/webclient/login/'
        client.get(URL)

        if 'csrftoken' in client.cookies:
            # Django 1.6 and up
            csrftoken = client.cookies['csrftoken']
        else:
            # older versions
            csrftoken = client.cookies['csrf']

        data = {'username': username,
                'password': password,
                'server': server,
                'csrfmiddlewaretoken': csrftoken}

        response = client.post(URL, headers=headers, data=data)
        if response.status_code == 200:
            self.client = client
        else:
            self.client = None
