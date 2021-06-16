from app import app
from db import Database
if __name__ == '__main__':
    db = Database()
    success = db.make_table()
    if not success:
        print("Database creation failed")
    else:
        app.run()