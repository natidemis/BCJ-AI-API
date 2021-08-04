"""
@author natidemis
June 2021

script for generating a secret token
"""
import secrets
import os.path
import logging
import gdown
from log import logger

def main():
    GOOGLE_NEWS = 'GoogleNews-vectors-negative300.bin'

    logger.info('Looking for google news vectors..')

    if not os.path.exists(GOOGLE_NEWS):
        try:
            logger.info('Fetching google news vectors')
            GOOGLE_NEWS_URL = ("https://drive.google.com/u/3/uc?"
            "id=1px8wUBO5KF7vjcO609bkQT1AMKNaF5vs&export=download")
            gdown.download(GOOGLE_NEWS_URL, GOOGLE_NEWS, quiet=False)
        except ValueError:
            logger.error("Failed to fetch the vectors.")
    else:
        logging.info("Google news vectors file is already in path")

    with open('.env', 'w') as f:
        f.write('DEBUG = False \nSECRET_TOKEN = {}\n'.format(secrets.token_urlsafe(100)))
        f.write('GOOGLENEWS_PATH = ./GoogleNews-vectors-negative300.bin\n')
        f.write('DATASET = googlenews')

if __name__ == '__main__':
    main()