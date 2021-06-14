from dotenv import load_dotenv
import psycopg2
import os
import dotenv

load_dotenv()


class Database:
    CREATED = False
    HOST = os.getenv('DB_HOST')
    NAME = os.getenv('DB_NAME')
    USER = os.getenv('DB_USER')
    PASSWORD = os.getenv('DB_PASSWORD')
    Vector = list[float]
    def __init__(self):
        """
        Class to setup the database table when required.
        """
    
    async def make_table(self, size: int) -> bool:
        """
        One time use to set up the Vectors table, 
        required to determine vector length.
        """
        if self.CREATED:
            return False
        sql_file = open('sql/schema.sql','r')
        schema = sql_file.read()
        sql_file.close()
        try:
            await conn = psycopg2.connect(dbname=self.NAME,user=self.USER, password=self.PASSWORD, host=self.HOST)
            cur = conn.cursor()
            await cur.execute(schema,[size], async_ = True)
            conn.commit()
            await cur.close()
            await conn.close()
            self.CREATED = True
            return True
        except:
            return False

    def insert(self,id: int,vec: Vector, bucket: str) -> bool:
        sql_file = open('sql/insert.sql','r')
        query = sql_file.read()
        sql_file.close()
        try:
            conn = psycopg2.connect(dbname=self.NAME,user=self.USER, password=self.PASSWORD, host=self.HOST)
            cur = conn.cursor()
            cur.execute(query,(id,vec,bucket))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except:
            return False