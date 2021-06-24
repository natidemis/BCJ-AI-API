from app import app
from db import Database
import logging

logging.getLogger().setLevel(logging.INFO)
if __name__ == '__main__':
    db = Database()
    db.drop_table()
    success = db.make_table()
    if not success:
        logging.error("Setting up the database failed, server will not run.")
    else:
        logging.info("Database initialized successfully, starting app..")
        app.run()