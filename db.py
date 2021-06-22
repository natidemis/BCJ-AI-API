from dotenv import load_dotenv
import asyncpg
import asyncio
import os
import dotenv
import Enum
from helper import QueryString 
from datetime import datetime
import logging

load_dotenv()

logging.getLogger().setLevel(logging.INFO)

class Database:
  
     def __init__(self):
        """
        Class to setup the database table when required.
        """
        self.HOST = os.getenv('DB_HOST')
        self.NAME = os.getenv('DB_NAME')
        self.USER = os.getenv('DB_USER')
        self.PASSWORD = os.getenv('DB_PASSWORD')
        self.NULL = "NULL"
    async def __make_table(self) -> bool:
        """
        Asyncronous function to create the table 

        Returns
        -------
        True if table creation successful, false otherwise
        """
        sql_file = open('sql/schema.sql','r')
        query = sql_file.read()
        sql_file.close()

        try:
            conn = await asyncpg.connect('postgres://{}:{}@{}/{}'.format(self.USER,self.PASSWORD,self.HOST,self.NAME))
            await conn.execute(query)
            await conn.close()
            logging.info("Table created.")
            return True
        except:
            logging.error("Creating table failed, re-evaluate query string")
            return False


    async def __insert(self, id: int,date: str, summary: list = None,descr: list = None, bucket: str= None) -> bool:
        """
        Async method for inserting into the database

        Returns
        -------
        True if insertion is successful, false otherwise
        """
 
        try:
            conn = await asyncpg.connect('postgres://{}:{}@{}/{}'.format(self.USER,self.PASSWORD,self.HOST,self.NAME))
            if bool(summary) and bool(descr) and bool(bucket):
                await conn.execute(QueryString.INSERT,id,summary,descr,bucket,datetime.fromisoformat(date))
            elif bool(summary) and bool(descr) and not bool(bucket):
                await conn.execute(QueryString.INSERT,id,summary,descr,self.NULL,datetime.fromisoformat(date))
            elif bool(summary) and not bool(descr) and bool(bucket)
                await conn.execute(QueryString.INSERT,id,summary,self.NULL,bucket,datetime.fromisoformat(date))
            elif bool(summary) and not bool(descr) and not bool(bucket):
                await conn.execute(QueryString.INSERT,id,summary,self.NULL,self.NULL,datetime.fromisoformat(date))
            elif bool(summary) and bool(descr) and bool(bucket):
                await conn.execute(QueryString.INSERT,id,self.NULL,descr,bucket,datetime.fromisoformat(date))
            elif bool(summary) and bool(descr) and not bool(bucket):
                await conn.execute(QueryString.INSERT,id,self.NULL,descr,self.NULL,datetime.fromisoformat(date))
            elif bool(summary) and not bool(descr) and bool(bucket)
                await conn.execute(QueryString.INSERT,id,self.NULL,self.NULL,bucket,datetime.fromisoformat(date))
            elif bool(summary) and not bool(descr) and not bool(bucket):
                await conn.execute(QueryString.INSERT,id,self.NULL,self.NULL,self.NULL,datetime.fromisoformat(date))
            await conn.close()
            logging.info("Insertion succcessful")
            return True
        except:
            logging.error("Failed to insert")
            return False
    
    async def __fetch_all(self) -> list:
        """
        Async method for fetching all rows in the database

        Returns
        -------
        a list of dict
        """

        try:
            conn = await asyncpg.connect('postgres://{}:{}@{}/{}'.format(self.USER,self.PASSWORD,self.HOST,self.NAME))
            rows = await conn.fetch(QueryString.FETCH)
            await conn.close()
            logging.info("Fetching succeeded")
            return [{'id': row['id'],'vector': row['vector'],'bucket': row['bucket']} for row in rows]
        except:
            logging.error("Fetching failed")
            return None
    async def __update(self, id: int, date: str, summary: str = None, descr: str=None, bucket: str=None) -> None:
        try: 
            conn = await asyncpg.connect('postgres://{}:{}@{}/{}'.format(self.USER,self.PASSWORD,self.HOST,self.NAME))
            if bool(summary) and bool(descr) and bool(bucket):
                await conn.execute(
                    QueryString.UPDATE_SUMM_AND_DESCR_W_BUCKET,
                    summary,
                    descr,
                    bucket,
                    datetime.fromisoformat(date),
                    id)
            elif bool(summary) and bool(descr) and not bool(bucket):
                await conn.execute(
                    QueryString.UPDATE_SUMM_AND_DESCR_NO_BUCKET,
                    summary,
                    descr,
                    datetime.fromisoformat(date),
                    id)
            elif bool(summary) and not bool(descr) and bool(bucket):
                await conn.execute(
                    QueryString.UPDATE_SUMM_W_BUCKET,
                    summary,
                    bucket,
                    datetime.fromisoformat(date),
                    id)
            elif bool(summary) and not bool(descr) and not bool(bucket):
                await conn.execute(
                    QueryString.UPDATE_SUMM_NO_BUCKET,
                    summary,
                    datetime.fromisoformat(date),
                    id)
            elif not bool(summary) and bool(descr) and bool(bucket):
                await conn.execute(
                    QueryString.UPDATE_DESCR_W_BUCKET,
                    descr,
                    bucket,
                    datetime.fromisoformat(date),
                    id)
            elif not bool(summary) and bool(descr) and not bool(bucket):
                await conn.execute(
                    QueryString.UPDATE_SUMM_W_BUCKET,
                    descr,
                    datetime.fromisoformat(date),
                    id)
            elif bool(bucket) and not bool(descr) and not bool(summary):
                await conn.execute(
                    QueryString.UPDATE_BUCKET_ONLY,
                    bucket,
                    datetime.fromisoformat(date),
                    id)
            conn.close()
            except:
                logging.error("Updating failed")
                return None

    async def __delete(self, id) -> None:
        """
        Removes a row from the database by ID

        Returns
        -------
        None
        """
        try:
            conn = await asyncpg.connect('postgres://{}:{}@{}/{}'.format(self.USER,self.PASSWORD,self.HOST,self.NAME))
            conn.execute(QueryString.DELETE,id)
            conn.close()
            logging.info("successfully deleted row")
        except:
            logging.info('Deletion error occured')
            pass


    def make_table(self) -> bool:
        """
        One time use to set up the Vectors table, 
        required to determine vector length.

        Returns
        -------
        True if table creation is successful, false otherwise
        """

        return asyncio.run(self.__make_table())

    def insert(self, id: int, vec: list, bucket: str) -> bool:
        """
        Method for inserting into the database

        Returns
        -------
        True if insertion successful, false otherwise
        """
        return asyncio.run(self.__insert(id=id,date=date,summary=summary,descr=descr,bucket=bucket))
    
    def fetch_all(self) -> list:
        """
        Fetches all rows in the table

        Returns
        -------
        All rows, None if a problem occurs
        """
        return asyncio.run(self.__fetch_all())
    def update(self, id: int, date: str, summary: str = None, descr: str=None, bucket: str=None) -> None:
        return asyncio.run(self.__update(id=id,date=date,summary=summary,descr=descr,bucket=bucket))
    
    def delete(self, id: int) -> None:
        return asyncio.run(self.__delete(id=id))