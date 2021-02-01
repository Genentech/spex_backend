from os import path, environ
from dotenv import dotenv_values

mode = environ.get('MODE')

file = '.env{}'.format('.{}'.format(mode) if mode else '')
local = '{}.local'.format(file)

config = {
    **dotenv_values(local if path.exists(local) else file)
}

trues = ['true', 'yes']
falses = ['false', 'no']

for key, value in config.items():
    environ[key] = value
    if value:
        if value.lower() in trues:
            value = True
            config[key] = value
        elif value.lower() in falses:
            value = False
            config[key] = value
