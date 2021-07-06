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

class Database:
  
    def __init__(self):
        """
        Class to setup the database table when required.
        """
        self.DATABASE_URL = os.getenv('DATABASE_URL')
    


    async def __make_table(self) -> bool:
        """
        Asyncronous function to create the table 

        Returns
        -------
        True if table creation successful, false otherwise
        """
        sql_file = open('sql/schema.sql','r')
        query = sql_file.read()
        query = query.split(';')
        sql_file.close()

        try:
            conn = await asyncpg.connect(self.DATABASE_URL)
            await conn.execute(query[0])
            await conn.execute(query[1])
            await conn.execute(query[2])
            await conn.close()
            logging.info("Table created.")
            return True
        except:
            logging.error("Creating table failed, re-evaluate enviroment variables.")
            return False


    async def __insert(self, id: int,date: str, summary: list = None,descr: list = None, batch_id: int= None) -> bool:
        """
        Async method for inserting into the database

        Returns
        -------
        True if insertion is successful, false otherwise
        """

        try:
            conn = await asyncpg.connect(self.DATABASE_URL)
            await conn.execute(QueryString.INSERT.value,id,summary,descr,batch_id,date)
            await conn.close()
            logging.info("Insertion succcessful")
            return True
        except(ValueError):
            logging.error("Failed to insert")
            return False

    async def __insert_batch(self,data) -> None:
        try:
            conn = await asyncpg.connect(self.DATABASE_URL)
            await conn.executemany(QueryString.INSERT.value,data)
            await conn.close()
            logging.info("Batch insertion successful")
            return True
        except(ValueError):
            logging.error("Failed to insert batch")
            return False

    
    async def __fetch_all(self) -> list:
        """
        Async method for fetching all rows in the database

        Returns
        -------
        a list of dict
        """

        try:
            conn = await asyncpg.connect(self.DATABASE_URL)
            rows = await conn.fetch(QueryString.FETCH.value)
            await conn.close()
            logging.info("Fetching all succeeded")
            return [{'id': row['id'],'summary': row['summary'],'description': row['descr'],'batch_id': row['batch_id'],'date': row['dateup']} for row in rows]
        except(ValueError):
            logging.error("Fetching all failed")
            return None
        
    async def __update(self, id: int, date: str, summary: str = None, descr: str=None, batch_id: int=None) -> None:
        try: 
            conn = await asyncpg.connect(self.DATABASE_URL)
            if bool(summary) and bool(descr) and bool(batch_id):
                await conn.execute(
                    QueryString.UPDATE_SUMM_AND_DESCR_W_BATCH.value,
                    summary,
                    descr,
                    batch_id,
                    date,
                    id)
            elif bool(summary) and bool(descr) and not bool(batch_id):
                await conn.execute(
                    QueryString.UPDATE_SUMM_AND_DESCR_NO_BATCH.value,
                    summary,
                    descr,
                    date,
                    id)
            elif bool(summary) and not bool(descr) and bool(batch_id):
                await conn.execute(
                    QueryString.UPDATE_SUMM_W_BATCH.value,
                    summary,
                    batch_id,
                    date,
                    id)
            elif bool(summary) and not bool(descr) and not bool(batch_id):
                await conn.execute(
                    QueryString.UPDATE_SUMM_NO_BATCH.value,
                    summary,
                    date,
                    id)
            elif not bool(summary) and bool(descr) and bool(batch_id):
                await conn.execute(
                    QueryString.UPDATE_DESCR_W_BATCH.value,
                    descr,
                    batch_id,
                    date,
                    id)
            elif not bool(summary) and bool(descr) and not bool(batch_id):
                await conn.execute(
                    QueryString.UPDATE_DESCR_NO_BATCH.value,
                    descr,
                    date,
                    id)
            elif bool(batch_id) and not bool(descr) and not bool(summary):
                await conn.execute(
                    QueryString.UPDATE_BATCH_ONLY.value,
                    batch_id,
                    date,
                    id)
            else:
                raise ValueError
            await conn.close()
            logging.info("Update successful")
            return True
        except(ValueError):
            logging.error("Updating failed")
            return False

    async def __delete(self, id: int) -> None:
        """
        Removes a row from the database by ID

        Returns
        -------
        None
        """
        try:
            conn = await asyncpg.connect(self.DATABASE_URL)
            result = await conn.fetch(QueryString.DELETE.value,id)
            await conn.close()
            logging.info("successfully deleted row")
            return result[0]['count']
        except:
            logging.info('Deletion error occured')
            return None
    async def __delete_batch(self,batch_id: int) -> int:
        """
        Removes all rows with batch_id

        Returns
        -------
        None
        """
        try:
            conn = await asyncpg.connect(self.DATABASE_URL)
            result = await conn.fetch(QueryString.DELETE_BATCH.value,batch_id)
            await conn.close()
            logging.info("successfully deleted row")
            return result[0]['count']
        except:
            logging.info('Deletion error occured')
            return None

    async def __drop_table(self):
        """
        Method for dropping table for each setup of the server in development mode.
        """
        try:
            q = "DROP TABLE IF EXISTS Vectors;"
            q1 = "DROP INDEX IF EXISTS vectors_id;"
            q2 = "DROP INDEX IF EXISTS vectors_batch;"
            conn = await asyncpg.connect(self.DATABASE_URL)
            await conn.execute(q)
            await conn.execute(q1)
            await conn.execute(q2)
            await conn.close()
            logging.info("Dropped table to avoid unnecessary errors.")
        except:
            logging.info("Error dropping table")
    
    def drop_table(self):
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.__drop_table())
        loop.close()
        return result
    
    def make_table(self) -> bool:
        """
        One time use to set up the Vectors table, 
        required to determine vector length.

        Returns
        -------
        True if table creation is successful, false otherwise
        """
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.__make_table())
        loop.close()
        return result

    def insert(self, id: int, date: str,batch_id: int=None, summary: list = None, descr: list=None) -> bool:
        """
        Method for inserting into the database

        Returns
        -------
        True if insertion successful, false otherwise
        """
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.__insert(id=id,date=date,summary=summary,descr=descr,batch_id=batch_id))
        loop.close()
        return result
    
    def fetch_all(self) -> list:
        """
        Fetches all rows in the table

        Returns
        -------
        All rows, None if a problem occurs
        """
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.__fetch_all())
        loop.close()
        return result
    
    def update(self, id: int, date: str, summary: str = None, descr: str=None, batch_id: int=None) -> None:
        """
        Update values of a row by id

        Returns
        -------
        Boolean, true if successfully updated, false otherwise
        """
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.__update(id=id,date=date,summary=summary,descr=descr,batch_id=batch_id))
        loop.close()
        return result
    
    def delete(self, id: int) -> None:
        """
        Delete row by id

        Returns
        -------
        Boolean, true if successful, false otherwise
        """
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.__delete(id=id))
        loop.close()
        return result
    
    def delete_batch(self, batch_id: int) -> None:
        """
        Delete row by batch_id

        Returns
        -------
        Boolean, true if successful, false otherwise
        """
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.__delete_batch(batch_id=batch_id))
        loop.close()
        return result

    def insert_batch(self, data) -> bool:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.__insert_batch(data))
        loop.close()
        return result   