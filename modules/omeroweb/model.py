import requests


class Proxy():
    client:  dict()

    def __init__(
        self,
        client:  dict = {},
        login: str = '',
        password: str = '',
    ):
        self.client = client
        self.login = login
        self.password = password

    def createFind(self, login, password):

        if self.client.get(login) is None:
            self.loginOmeroProxy(login, password)
            return self.client.get(login)
        elif self.client.get(login) is not None:
            return self.client.get(login)

    def loginOmeroProxy(self, login, password, server='1'):

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

        data = {'username': login,
                'password': password,
                'server': server,
                'csrfmiddlewaretoken': csrftoken}

        response = client.post(URL, headers=headers, data=data)
        if response.status_code == 200:
            self.client[login] = client
        else:
            del self.client[login]
