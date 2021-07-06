#Set up the database tables
from db import Database
db = Database()
db.drop_table() 
success = db.make_table()

#Fetch vectors for the models.
exec(open("./fetch_vectors.py").read())


#Run app
from app import app
import logging

logging.getLogger().setLevel(logging.INFO)


if __name__ == '__main__':
    if not success:
        logging.error("Setting up the database failed, server will not run.")
    else:
        logging.info("Database initialized successfully, starting app..")
        app.run()