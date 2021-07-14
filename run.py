"""
@authors: Gitcelo, natidemis
May 2021

File that executes the app and sets up the database.
"""
#Set up the database tables
import logging
from db import Database
db = Database()
#db.drop_table()
success = db.make_table()

#Fetch vectors for the models.
#exec(open("./fetch_vectors.py").read())

#Run app
from app import app # pylint: disable=wrong-import-position

logging.basicConfig(format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    if not success:
        logger.error("Setting up the database failed, server will not run.")
    else:
        logger.info("Database initialized successfully, starting app..")
        app.run()
else:
    gunicorn_app = app()
