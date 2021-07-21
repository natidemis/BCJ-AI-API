# pylint: disable=W0703
"""
@author natidemis
June 2021

Contains the database class used for setting up for and
making query to the database
"""

import os
import asyncio
from typing import Union, List
from dotenv import load_dotenv
import asyncpg
from log import logger
from helper import QueryString

load_dotenv()


asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class Database:
    """
    Class for handling database connection and queries
    """
    def __init__(self):
        """
        Class to setup the database table when required.
        """
        self.database_url = os.getenv('DATABASE_URL')



    async def __make_table(self) -> bool:
        """
        Asyncronous function to create the table

        Returns
        -------
        True if table creation successful, false otherwise
        """
        with open('sql/schema.sql','r') as sql_file:
            query = sql_file.read()
            queries = query.split(';')

        try:
            conn = await asyncpg.connect(self.database_url)
            await conn.execute(queries[0])
            await conn.execute(queries[1])
            await conn.execute(queries[2])
            await conn.close()
            logger.info("Checking and/or setting up database complete.")
            return True
        except RuntimeError:
            logger.error("Setting up database failed, re-evaluate enviroment variables.")
            return False


    async def __insert(self,
                        _id: int,
                        user_id: str,
                        embeddings: List[Union[int,float]] = None,
                        batch_id: int= None) -> None:
        """
        Async method for inserting into the database

        Returns
        -------
        True if insertion is successful, false otherwise
        """

        try:
            conn = await asyncpg.connect(self.database_url)
            await conn.execute(QueryString.INSERT.value,_id,user_id,embeddings,batch_id)
            await conn.close()
            logger.info("Insertion successful")
        except Exception:
            logger.error("Failed to insert")
            raise ValueError from Exception

    async def __insert_batch(self,data) -> bool:
        try:
            conn = await asyncpg.connect(self.database_url)
            await conn.executemany(QueryString.INSERT.value,data)
            await conn.close()
            logger.info("Batch insertion successful")
            return True
        except Exception:
            logger.error("Failed to insert batch")
            raise ValueError from Exception


    async def __fetch_all(self) -> Union[list,None]:
        """
        Async method for fetching all rows in the database

        Returns
        -------
        a list of dict
        """

        try:
            conn = await asyncpg.connect(self.database_url)
            rows = await conn.fetch(QueryString.FETCH.value)
            await conn.close()
            logger.info("Fetching all succeeded")
            return [{'id': row['id'],
                    'summary': row['summary'],
                    'description': row['descr'],
                    'batch__id': row['batch_id'],
                    'date': row['dateup']} for row in rows]
        except Exception:
            logger.error("Fetching all failed")
            return None

    async def __update(self,
                        _id: int,
                        date: str,
                        summary: str = None,
                        descr: str=None,
                        batch__id: int=None) -> None:
        try:
            conn = await asyncpg.connect(self.database_url)
            if bool(summary) and bool(descr) and bool(batch__id):
                await conn.execute(
                    QueryString.UPDATE_SUMM_AND_DESCR_W_BATCH.value,
                    summary,
                    descr,
                    batch__id,
                    date,
                    _id)
            elif bool(summary) and bool(descr) and not bool(batch__id):
                await conn.execute(
                    QueryString.UPDATE_SUMM_AND_DESCR_NO_BATCH.value,
                    summary,
                    descr,
                    date,
                    _id)
            elif bool(summary) and not bool(descr) and bool(batch__id):
                await conn.execute(
                    QueryString.UPDATE_SUMM_W_BATCH.value,
                    summary,
                    batch__id,
                    date,
                    _id)
            elif bool(summary) and not bool(descr) and not bool(batch__id):
                await conn.execute(
                    QueryString.UPDATE_SUMM_NO_BATCH.value,
                    summary,
                    date,
                    _id)
            elif not bool(summary) and bool(descr) and bool(batch__id):
                await conn.execute(
                    QueryString.UPDATE_DESCR_W_BATCH.value,
                    descr,
                    batch__id,
                    date,
                    _id)
            elif not bool(summary) and bool(descr) and not bool(batch__id):
                await conn.execute(
                    QueryString.UPDATE_DESCR_NO_BATCH.value,
                    descr,
                    date,
                    _id)
            elif bool(batch__id) and not bool(descr) and not bool(summary):
                await conn.execute(
                    QueryString.UPDATE_BATCH_ONLY.value,
                    batch__id,
                    date,
                    _id)
            else:
                raise ValueError
            await conn.close()
            logger.info("Update successful")
        except Exception:
            logger.error("Updating failed")
            raise ValueError from Exception

    async def __delete(self, _id: int) -> None:
        """
        Removes a row from the database by _ID

        Returns
        -------
        None
        """
        try:
            conn = await asyncpg.connect(self.database_url)
            result = await conn.fetch(QueryString.DELETE.value,_id)
            await conn.close()
            logger.info("successfully deleted row")
            return result[0]['count']
        except Exception:
            logger.info('Deletion error occured')
            return None
    async def __delete_batch(self,batch__id: int) -> Union[int,None]:
        """
        Removes all rows with batch__id

        Returns
        -------
        None
        """
        try:
            conn = await asyncpg.connect(self.database_url)
            result = await conn.fetch(QueryString.DELETE_BATCH.value,batch__id)
            await conn.close()
            logger.info("successfully deleted row")
            return result[0]['count']
        except Exception:
            logger.info('Deletion error occured')
            return None

    async def __drop_table(self):
        """
        Method for dropping table for each setup of the server in development mode.
        """
        try:
            query_ = "DROP TABLE IF EXISTS Vectors;"
            query_1 = "DROP INDEX IF EXISTS vectors_id;"
            query_2 = "DROP INDEX IF EXISTS vectors_batch;"
            conn = await asyncpg.connect(self.database_url)
            await conn.execute(query_)
            await conn.execute(query_1)
            await conn.execute(query_2)
            await conn.close()
            logger.info("Dropped table to avoid unnecessary errors.")
        except Exception:
            logger.info("Error dropping table")

    def drop_table(self):
        """
        Method for dropping the table
        """

        result = asyncio.run(self.__drop_table())
        return result

    def make_table(self) -> bool:
        """
        One time use to set up the Vectors table,
        required to determine vector length.

        Returns
        -------
        True if table creation is successful, false otherwise
        """

        result = asyncio.run(self.__make_table())
        return result

    def insert(self,
                _id: int,
                date: str,
                batch__id: int=None,
                summary: list = None,
                descr: list=None) -> None:
        """
        Method for inserting into the database

        Returns
        -------
        True if insertion successful, false otherwise
        """

        asyncio.run(self.__insert(
                                _id=_id,
                                date=date,
                                summary=summary,
                                descr=descr,
                                batch__id=batch__id))

    def fetch_all(self) -> Union[list,None]:
        """
        Fetches all rows in the table

        Returns
        -------
        All rows, None if a problem occurs
        """

        result = asyncio.run(self.__fetch_all())
        return result

    def update(
            self,
            _id: int,
            date: str,
            summary: str = None, descr: str=None, batch__id: int=None) -> None:
        """
        Update values of a row by _id

        Returns
        -------
        Boolean, true if successfully updated, false otherwise
        """

        asyncio.run(self.__update(
                                _id=_id,
                                date=date,
                                summary=summary,
                                descr=descr,
                                batch__id=batch__id))


    def delete(self, _id: int) -> None:
        """
        Delete row by _id

        Returns
        -------
        Boolean, true if successful, false otherwise
        """

        result = asyncio.run(self.__delete(_id=_id))
        return result

    def delete_batch(self, batch__id: int) -> Union[int,None]:
        """
        Delete row by batch__id

        Returns
        -------
        Boolean, true if successful, false otherwise
        """

        result = asyncio.run(self.__delete_batch(batch__id=batch__id))
        return result

    def insert_batch(self, data) -> bool:
        """
        Method for inserting a batch of data

        Returns
        -------
        Number of inserted data
        """

        result = asyncio.run(self.__insert_batch(data))
        return result
