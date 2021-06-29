from db import Database
db = Database()
#db.drop_table() #fjarlægja seinna
success = db.make_table()

from app import app
import logging

logging.getLogger().setLevel(logging.INFO)
if __name__ == '__main__':
    if not success:
        logging.error("Setting up the database failed, server will not run.")
    else:
        logging.info("Database initialized successfully, starting app..")
        app.run()