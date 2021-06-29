from dotenv import load_dotenv
import asyncpg
import asyncio
import os
import dotenv
from enum import Enum
from helper import QueryString 
from datetime import datetime
import logging

load_dotenv()

logging.getLogger().setLevel(logging.INFO)
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class Database:
  
    def __init__(self):
        """
        Class to setup the database table when required.
        """
        self.HOST = os.getenv('DB_HOST')
        self.NAME = os.getenv('DB_NAME')
        self.USER = os.getenv('DB_USER')
        self.PASSWORD = os.getenv('DB_PASSWORD')

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
            logging.error("Creating table failed, re-evaluate enviroment variables.")
            return False


    async def __insert(self, id: str,date: str, summary: list = None,descr: list = None, bucket: str= None) -> bool:
        """
        Async method for inserting into the database

        Returns
        -------
        True if insertion is successful, false otherwise
        """

        try:
            conn = await asyncpg.connect('postgres://{}:{}@{}/{}'.format(self.USER,self.PASSWORD,self.HOST,self.NAME))
            await conn.execute(QueryString.INSERT.value,id,summary,descr,bucket,date)
            await conn.close()
            logging.info("Insertion succcessful")
            return True
        except(ValueError):
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
            rows = await conn.fetch(QueryString.FETCH.value)
            await conn.close()
            logging.info("Fetching all succeeded")
            return [{'id': row['id'],'summary': row['summary'],'description': row['descr'],'bucket': row['bucket'],'date': row['dateup']} for row in rows]
        except(ValueError):
            logging.error("Fetching all failed")
            return None
        
    async def __update(self, id: str, date: str, summary: str = None, descr: str=None, bucket: str=None) -> None:
        try: 
            conn = await asyncpg.connect('postgres://{}:{}@{}/{}'.format(self.USER,self.PASSWORD,self.HOST,self.NAME))
            if bool(summary) and bool(descr) and bool(bucket):
                await conn.execute(
                    QueryString.UPDATE_SUMM_AND_DESCR_W_BUCKET.value,
                    summary,
                    descr,
                    bucket,
                    date,
                    id)
            elif bool(summary) and bool(descr) and not bool(bucket):
                await conn.execute(
                    QueryString.UPDATE_SUMM_AND_DESCR_NO_BUCKET.value,
                    summary,
                    descr,
                    date,
                    id)
            elif bool(summary) and not bool(descr) and bool(bucket):
                await conn.execute(
                    QueryString.UPDATE_SUMM_W_BUCKET.value,
                    summary,
                    bucket,
                    date,
                    id)
            elif bool(summary) and not bool(descr) and not bool(bucket):
                await conn.execute(
                    QueryString.UPDATE_SUMM_NO_BUCKET.value,
                    summary,
                    date,
                    id)
            elif not bool(summary) and bool(descr) and bool(bucket):
                await conn.execute(
                    QueryString.UPDATE_DESCR_W_BUCKET.value,
                    descr,
                    bucket,
                    date,
                    id)
            elif not bool(summary) and bool(descr) and not bool(bucket):
                await conn.execute(
                    QueryString.UPDATE_DESCR_NO_BUCKET.value,
                    descr,
                    date,
                    id)
            elif bool(bucket) and not bool(descr) and not bool(summary):
                await conn.execute(
                    QueryString.UPDATE_BUCKET_ONLY.value,
                    bucket,
                    date,
                    id)
            await conn.close()
            logging.info("Update successful")
            return True
        except(ValueError):
            logging.error("Updating failed")
            return False

    async def __delete(self, id: str) -> None:
        """
        Removes a row from the database by ID

        Returns
        -------
        None
        """
        try:
            conn = await asyncpg.connect('postgres://{}:{}@{}/{}'.format(self.USER,self.PASSWORD,self.HOST,self.NAME))
            await conn.execute(QueryString.DELETE.value,id)
            await conn.close()
            logging.info("successfully deleted row")
        except:
            logging.info('Deletion error occured')
    async def __delete_bucket(self,bucket_id: str) -> None:
        """
        Removes all rows with bucket_id

        Returns
        -------
        None
        """
        try:
            conn = await asyncpg.connect('postgres://{}:{}@{}/{}'.format(self.USER,self.PASSWORD,self.HOST,self.NAME))
            await conn.execute(QueryString.DELETE_BUCKET.value,bucket_id)
            await conn.close()
            logging.info("successfully deleted row")
            return True
        except:
            logging.info('Deletion error occured')
            return False

    async def __drop_table(self):
        """
        Method for dropping table for each setup of the server in development mode.
        """
        try:
            q = "DROP TABLE IF EXISTS Vectors;"
            conn = await asyncpg.connect('postgres://{}:{}@{}/{}'.format(self.USER,self.PASSWORD,self.HOST,self.NAME))
            await conn.execute(q)
            await conn.close()
            logging.info("Dropped table to avoid unnecessary errors.")
        except:
            logging.info("Error dropping table")
    
    def drop_table(self):
        return asyncio.run(self.__drop_table())
    
    def make_table(self) -> bool:
        """
        One time use to set up the Vectors table, 
        required to determine vector length.

        Returns
        -------
        True if table creation is successful, false otherwise
        """

        return asyncio.run(self.__make_table())

    def insert(self, id: str, date: str,bucket: str=None, summary: list = None, descr: list=None) -> bool:
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
    
    def update(self, id: str, date: str, summary: str = None, descr: str=None, bucket: str=None) -> None:
        """
        Update values of a row by id

        Returns
        -------
        Boolean, true if successfully updated, false otherwise
        """
        return asyncio.run(self.__update(id=id,date=date,summary=summary,descr=descr,bucket=bucket))
    
    def delete(self, id: str) -> None:
        """
        Delete row by id

        Returns
        -------
        Boolean, true if successful, false otherwise
        """
        return asyncio.run(self.__delete(id=id))
    
    def delete_bucket(self, bucket_id: str) -> None:
        """
        Delete row by id

        Returns
        -------
        Boolean, true if successful, false otherwise
        """

        return asyncio.run(self.__delete_bucket(bucket_id=bucket_id))
    