import gdown
import os.path
import logging

logging.basicConfig(format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)

npyvector = 'wordvectors.wv.vectors.npy' 

gensimvector = 'wordvectors.wv'

logger.info('Looking for vectors..')

if not os.path.exists(npyvector):
    try:
        logger.info('Fetching numpy vectors')
        npy_url = 'https://drive.google.com/uc?id=1Izx4in1jUvI1-tCV5S-brZrse_HRwgVj' #sharable drive link
        gdown.download(npy_url, npyvector, quiet=False)
    except:
        logger.error("Failed to fetch numpy vectors.")
else:
    logging.info("Numpy vectors already in path")
if not os.path.exists(gensimvector):
    try:
        logger.info('Fetching gensim vectors')
        gensim_url = 'https://drive.google.com/uc?id=1QMwcpvnSMFq_VikgzPzK0QcZ6kqmXy2p' #sharable drive link
        gdown.download(gensim_url,gensimvector, quiet=False)
    except:
        logger.error("Fetching gensim vectors failed.")
else:
    logger.info("Gensim vectors already in path.")


