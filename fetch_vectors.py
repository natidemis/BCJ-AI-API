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

NUMPY_VECTOR = 'wordvectors.wv.vectors.npy'

GENSIM_VECTOR = 'wordvectors.wv'

logger.info('Looking for vectors..')

if not os.path.exists(NUMPY_VECTOR):
    try:
        logger.info('Fetching numpy vectors')
        NUMPY_URL = 'https://drive.google.com/uc?id=1Izx4in1jUvI1-tCV5S-brZrse_HRwgVj'
        gdown.download(NUMPY_URL, NUMPY_VECTOR, quiet=False)
    except ValueError:
        logger.error("Failed to fetch numpy vectors.")
else:
    logging.info("Numpy vectors already in path")
if not os.path.exists(GENSIM_VECTOR):
    try:
        logger.info('Fetching gensim vectors')
        GENSIM_URL = 'https://drive.google.com/uc?id=1QMwcpvnSMFq_VikgzPzK0QcZ6kqmXy2p'
        gdown.download(GENSIM_URL,GENSIM_VECTOR, quiet=False)
    except ValueError:
        logger.error("Fetching gensim vectors failed.")
else:
    logger.info("Gensim vectors already in path.")
