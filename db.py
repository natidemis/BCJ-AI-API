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



    async def _make_table(self) -> bool:
        """
        Asyncronous function to create the table

        Returns
        -------
        True if table creation successful, false otherwise
        """
        with open('sql/schema.sql','r') as sql_file:
            query = sql_file.read()

        try:
            conn = await asyncpg.connect(self.database_url)
            await conn.execute(query)
            await conn.close()
            logger.info("Checking and/or setting up database complete.")
            return True
        except RuntimeError:
            logger.error("Setting up database failed, re-evaluate enviroment variables.")
            return False


    async def _insert(self,
                        _id: int,
                        user_id: str,
                        embeddings: List[Union[int,float]],
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
            logger.info("Insertng data successful")
        except Exception:
            logger.error("Failed to insert data")
            raise ValueError from Exception

    async def _insert_user(self, user_id: int) -> None:
        """
        Async method for inserting a user into the database

        Returns
        -------
        True if insertion is successful, false otherwise
        """

        try:
            conn = await asyncpg.connect(self.database_url)
            await conn.execute(QueryString.INSERT_USER.value,user_id)
            await conn.close()
            logger.info("Inserting user successful")
        except Exception:
            logger.error("Failed to insert user")
            raise ValueError from Exception

    async def _insert_batch(self,data) -> bool:
        try:
            conn = await asyncpg.connect(self.database_url)
            await conn.executemany(QueryString.INSERT.value,data)
            await conn.close()
            logger.info("Batch insertion successful")
            return True
        except Exception:
            logger.error("Failed to insert batch")
            raise ValueError from Exception


    async def _fetch_all(self, user_id: str) -> Union[list,None]:
        """
        Async method for fetching all rows in the database

        Returns
        -------
        a list of dict
        """

        try:
            conn = await asyncpg.connect(self.database_url)
            rows = await conn.fetch(QueryString.FETCH.value,user_id)
            await conn.close()
            logger.info("Fetching all succeeded")
            return [{'id': row['id'],
                    'embeddings': row['embeddings'],
                    'batch_id': row['batch_id']} for row in rows]
        except Exception:
            logger.error("Fetching all failed")
            return None

    async def _update(self,
                        _id: int,
                        user_id: int,
                        embeddings: List[Union[int,float]] = None,
                        batch_id: int=None) -> None:
        try:
            conn = await asyncpg.connect(self.database_url)
            if bool(batch_id) and bool(embeddings):
                await conn.execute(
                    QueryString.UPDATE_EMBS_W_BATCH.value,
                    embeddings,
                    batch_id,
                    _id,
                    user_id
                    )
            elif bool(batch_id) and not bool(embeddings):
                await conn.execute(
                    QueryString.UPDATE_NO_BATCH.value,
                    batch_id,
                    _id,
                    user_id
                    )
            elif not bool(batch_id) and bool(embeddings):
                await conn.execute(
                    QueryString.UPDATE_NO_BATCH_W_EMBS.value,
                    embeddings,
                    _id,
                    user_id
                    )
            await conn.close()
            logger.info("Update successful")
        except Exception:
            logger.error("Updating failed")
            raise ValueError('Updating failed.') from Exception

    async def _delete(self, _id: int, user_id: int) -> None:
        """
        Removes a row from the database by _ID

        Returns
        -------
        None
        """
        try:
            conn = await asyncpg.connect(self.database_url)
            result = await conn.fetch(QueryString.DELETE.value,_id,user_id)
            await conn.close()
            logger.info("successfully deleted row")
            return result[0]['count']
        except Exception:
            logger.info('Deletion error occured')
            return None
    async def _delete_batch(self,batch_id: int,user_id: int) -> Union[int,None]:
        """
        Removes all rows with batch_id

        Returns
        -------
        None
        """
        try:
            conn = await asyncpg.connect(self.database_url)
            result = await conn.fetch(QueryString.DELETE_BATCH.value,batch_id,user_id)
            await conn.close()
            logger.info("successfully deleted row")
            return result[0]['count']
        except Exception:
            logger.info('Deletion error occured')
            return None

    async def _drop_table(self):
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

    async def _fetch_users(self) -> List[int]:
        """
        Async method for fetching all users in the database

        Returns
        -------
        a list of dict
        """

        try:
            conn = await asyncpg.connect(self.database_url)
            rows = await conn.fetch(QueryString.FETCH_USERS.value)
            await conn.close()
            logger.info("Fetching all succeeded")
            return [row['user_id'] for row in rows]
        except Exception:
            logger.error("Fetching all failed")
            return None

    def drop_table(self):
        """
        Method for dropping the table
        """

        result = asyncio.run(self._drop_table())
        return result

    def make_table(self) -> bool:
        """
        One time use to set up the Vectors table,
        required to determine vector length.

        Returns
        -------
        True if table creation is successful, false otherwise
        """

        result = asyncio.run(self._make_table())
        return result

    def insert(self,
                _id: int,
                user_id: str,
                embeddings: List[Union[int,float]],
                batch_id: int= None) -> None:
        """
        Method for inserting into the database

        Returns
        -------
        True if insertion successful, false otherwise
        """

        asyncio.run(self._insert(
                                _id=_id,
                                user_id = user_id,
                                embeddings=embeddings,
                                batch_id=batch_id))

    def insert(self,user_id: int) -> None:
        """
        Method for inserting user into database

        Returns
        -------
        True if insertion successful, false otherwise
        """

        asyncio.run(self._insert_user(user_id=user_id))

    def fetch_all(self,user_id) -> Union[list,None]:
        """
        Fetches all rows in the table

        Returns
        -------
        All rows, None if a problem occurs
        """

        result = asyncio.run(self._fetch_all(user_id=user_id))
        return result

    def update(self,
                _id: int,
                user_id: int,
                embeddings: List[Union[int,float]] = None,
                batch_id: int=None) -> None:
        """
        Update values of a row by _id

        Returns
        -------
        Boolean, true if successfully updated, false otherwise
        """

        asyncio.run(self._update(
                                _id=_id,
                                date=date,
                                summary=summary,
                                descr=descr,
                                batch_id=batch_id))


    def delete(self, _id: int, user_id: int) -> None:
        """
        Delete row by _id

        Returns
        -------
        Boolean, true if successful, false otherwise
        """

        result = asyncio.run(self._delete(_id=_id,user_id=user_id))
        return result

    def delete_batch(self, batch_id: int,user_id) -> Union[int,None]:
        """
        Delete row by batch_id

        Returns
        -------
        Boolean, true if successful, false otherwise
        """

        result = asyncio.run(self._delete_batch(batch_id=batch_id,user_id=user_id))
        return result

    def insert_batch(self, data: List[tuple]) -> bool:
        """
        Method for inserting a batch of data

        Returns
        -------
        Number of inserted data
        """

        result = asyncio.run(self._insert_batch(data))
        return result

    def fetch_users() -> List[int]:
        """
        Fetch all users in the database

        Returns
        -------
        a list of user ids
        """

        return asyncio.run(self._fetch_users())
  