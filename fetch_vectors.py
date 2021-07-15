"""
@author natidemis
June 2021

Script for downloading gensim and numpy vectors from drive
"""
import os.path
import logging
import gdown

logging.basicConfig(format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)

GOOGLE_NEWS = 'GoogleNews-vectors-negative300.bin'

logger.info('Looking for google news vectors..')

if not os.path.exists(GOOGLE_NEWS):
    try:
        logger.info('Fetching google news vectors')
        GOOGLE_NEWS_URL = 'https://drive.google.com/u/3/uc?id=1px8wUBO5KF7vjcO609bkQT1AMKNaF5vs&export=download'
        gdown.download(GOOGLE_NEWS_URL, GOOGLE_NEWS, quiet=False)
    except ValueError:
        logger.error("Failed to fetch the vectors.")
else:
    logging.info("Google news vectors file is already in path")

