"""
@authors: Gitcelo, natidemis
May 2021

File that executes the app and sets up the database.
"""
#Set up the database tables
import fetch_vectors #pylint: disable=W0611
from log import logger
logger.info('Starting server..')
from db import Database #pylint: disable=C0413
db = Database()
#db.drop_table()
table_created = db.make_table()

#Run app
from app import app # pylint: disable=wrong-import-position

if __name__ == '__main__':
    if not table_created:
        logger.error("Setting up the database failed, server will not run.")
    else:
        logger.info("Database initialized successfully, starting app..")
        app.run()
else:
    gunicorn_app = app()
