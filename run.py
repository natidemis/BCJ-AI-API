from app import app
from db import Database
import logging
if __name__ == '__main__':
    db = Database()
    success = db.make_table()
    if not success:
        logging.error("Setting up the database failed, server will not run.")
    else:
        logging.info("Database initialized successfully, starting app..")
        app.run()