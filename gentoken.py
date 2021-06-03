import secrets

with open('config.py', 'w') as f:
    f.write('DEBUG = True \nSECRET_TOKEN = "{}"'.format(secrets.token_urlsafe(100)))

