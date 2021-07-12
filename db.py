"""
@author nat_idemis
June 2021

Contains the database class used for setting up for and
making query to the database
"""
import os
import asyncio
import logging
from dotenv import load_dotenv
import asyncpg
from helper import QueryString

load_dotenv()

logging.basicConfig(format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)

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
            query = query.split(';')

        try:
            conn = await asyncpg.connect(self.database_url)
            await conn.execute(query[0])
            await conn.execute(query[1])
            await conn.execute(query[2])
            await conn.close()
            logger.info("Table created.")
            return True
        except RuntimeError:
            logger.error("Creating table failed, re-evaluate enviroment variables.")
            return False


    async def __insert(self,
                        _id: int,
                        date: str,
                        summary: list = None,
                        descr: list = None,
                        batch__id: int= None) -> bool:
        """
        Async method for inserting into the database

        Returns
        -------
        True if insertion is successful, false otherwise
        """

        try:
            conn = await asyncpg.connect(self.database_url)
            await conn.execute(QueryString.INSERT.value,_id,summary,descr,batch__id,date)
            await conn.close()
            logger.info("Insertion successful")
            return True
        except RuntimeError:
            logger.error("Failed to insert")
            return False

    async def __insert_batch(self,data) -> None:
        try:
            conn = await asyncpg.connect(self.database_url)
            await conn.executemany(QueryString.INSERT.value,data)
            await conn.close()
            logger.info("Batch insertion successful")
            return True
        except RuntimeError:
            logger.error("Failed to insert batch")
            return False


    async def __fetch_all(self) -> list:
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
        except RuntimeError:
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
            return True
        except RuntimeError:
            logger.error("Updating failed")
            return False

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
        except RuntimeError:
            logger.info('Deletion error occured')
            return None
    async def __delete_batch(self,batch__id: int) -> int:
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
        except RuntimeError:
            logger.info('Deletion error occured')
            return None

    async def __drop_table(self):
        """
        Method for dropping table for each setup of the server in development mode.
        """
        try:
            query_ = "DROP TABLE IF EXISTS Vectors;"
            query_1 = "DROP INDEX IF EXISTS vectors__id;"
            query_2 = "DROP INDEX IF EXISTS vectors_batch;"
            conn = await asyncpg.connect(self.database_url)
            await conn.execute(query_)
            await conn.execute(query_1)
            await conn.execute(query_2)
            await conn.close()
            logger.info("Dropped table to avo_id unnecessary errors.")
        except RuntimeError:
            logger.info("Error dropping table")

    def drop_table(self):
        """
        Method for dropping the table
        """
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

    def insert(self,
                _id: int,
                date: str,
                batch__id: int=None,
                summary: list = None,
                descr: list=None) -> bool:
        """
        Method for inserting into the database

        Returns
        -------
        True if insertion successful, false otherwise
        """
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.__insert(
                                                    _id=_id,
                                                    date=date,
                                                    summary=summary,
                                                    descr=descr,
                                                    batch__id=batch__id))
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
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.__update(
                                                        _id=_id,
                                                        date=date,
                                                        summary=summary,
                                                        descr=descr,
                                                        batch__id=batch__id))
        loop.close()
        return result

    def delete(self, _id: int) -> None:
        """
        Delete row by _id

        Returns
        -------
        Boolean, true if successful, false otherwise
        """
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.__delete(_id=_id))
        loop.close()
        return result

    def delete_batch(self, batch__id: int) -> None:
        """
        Delete row by batch__id

        Returns
        -------
        Boolean, true if successful, false otherwise
        """
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.__delete_batch(batch__id=batch__id))
        loop.close()
        return result

    def insert_batch(self, data) -> bool:
        """
        Method for inserting a batch of data

        Returns
        -------
        Number of inserted data
        """
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.__insert_batch(data))
        loop.close()
        return result
