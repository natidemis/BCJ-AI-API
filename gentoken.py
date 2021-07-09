"""
@author natidemis
June 2021

script for generating a secret token
"""
import secrets

with open('.env', 'w') as f:
    f.write('DEBUG = False \nSECRET_TOKEN = {}'.format(secrets.token_urlsafe(100)))
