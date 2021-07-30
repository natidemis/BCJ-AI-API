"""
@authors: Gitcelo, natidemis
May 2021

File that executes the app and sets up the database.
"""
#Set up the database tables

from log import logger
from db import Database #pylint: disable=C0413
logger.info('Starting server..')
db = Database()
db.drop_table()
table_created = db.make_table()

#Run app
from app import app # pylint: disable=wrong-import-position

def main():
    """
    Starts app for development.
    """
    if table_created:
        logger.info("Database initialized successfully, starting app in development..")
        app.run()
    else:
        logger.error("Setting up the database failed, app will not run in development")

def gunicorn():
    """
    Method called when starting app in production.
    """
    if table_created:
        logger.info('Starting gunicorn app..')
        gunicorn_app = app()
    else:
        logger.error('Failed to start gunicorn app..')

if __name__ == '__main__':
    main()
else:
    gunicorn()
