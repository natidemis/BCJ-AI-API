import gdown
import os.path
import logging

logging.getLogger().setLevel(logging.INFO)

npyvector = 'wordvectors.wv.vectors.npy' 

gensimvector = 'wordvectors.wv'

logging.info('Looking for vectors..')

if not os.path.exists(npyvector):
    try:
        logging.info('Fetching numpy vectors')
        npy_url = 'https://drive.google.com/uc?id=1Izx4in1jUvI1-tCV5S-brZrse_HRwgVj' #sharable drive link
        gdown.download(npy_url, npyvector, quiet=False)
    except:
        logging.error("Failed to fetch numpy vectors.")
else:
    logging.info("Numpy vectors already in path")
if not os.path.exists(gensimvector):
    try:
        logging.info('Fetching gensim vectors')
        gensim_url = 'https://drive.google.com/uc?id=1QMwcpvnSMFq_VikgzPzK0QcZ6kqmXy2p' #sharable drive link
        gdown.download(gensim_url,gensimvector, quiet=False)
    except:
        logging.error("Fetching gensim vectors failed.")
else:
    logging.info("Gensim vectors already in path.")


