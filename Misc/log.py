"""
@authors: natidemis, stackoverflow
May 2021

File for logging purposes
"""
import logging

logger = logging.getLogger('server_logger')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('server.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(levelname)-8s [%(filename)s:%(lineno)d:%(asctime)s] %(message)s',
                                 datefmt='%Y-%m-%d %H:%M:%S')

ch.setFormatter(formatter)
fh.setFormatter(formatter)
# add the handlers to logger
logger.addHandler(ch)
logger.addHandler(fh)
