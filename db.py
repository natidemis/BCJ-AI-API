# pylint: disable=W0703
# pylint: disable=C0103
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

class NotFoundError(Exception):
    """
    Database error when return value is empty.
    """


class DuplicateKeyError(Exception):
    """
    Database error to raise when the key inserted already exists.
    """


class MissingArgumentError(Exception):
    """
    Database error when variables don't match the required columns.
    """

class NoUpdatesError(Exception):
    """
    Database error when a query makes no changes to the database.
    """



class AsyncpgSQL():
    """
    Context manager for asyncpg
    """
    def __init__(self, url):
        self._url = url
        self._conn = None

    async def __aenter__(self):
        self._conn = await asyncpg.connect(self._url)
        return self._conn

    async def __aexit__(self, exc_type, exc, tb): #closing the connection
        if self._conn:
            await self._conn.close()

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
            async with AsyncpgSQL(self.database_url) as conn:
                conn = await asyncpg.connect(self.database_url)
                await conn.execute(query)
                logger.info("Checking and/or setting up database complete.")
            return True
        except RuntimeError:
            logger.error("Setting up database failed, re-evaluate enviroment variables.")
            return False


    async def _insert(self,
                        _id: int,
                        user_id: int,
                        embeddings: List[Union[int,float]],
                        batch_id: int= None) -> None:
        """
        Async method for inserting into the database

        Returns
        -------
        True if insertion is successful, false otherwise
        """

        try:
            async with AsyncpgSQL(self.database_url) as conn:
                await conn.execute(QueryString.INSERT.value,_id,user_id,embeddings,batch_id)
            logger.info("Inserting data successful")

        except asyncpg.exceptions.UniqueViolationError as e:
            logger.error("Duplicate key error: %s for user_id: %s and id: %s",e,user_id,_id)
            raise DuplicateKeyError('Duplicate key error: %s' % e) from e
        except asyncpg.exceptions.ForeignKeyViolationError as e:
            logger.error('User_id does not exist in the Users database: %s,'
             'exception: %s',user_id,e)
            raise NotFoundError('User not in database: %s' % e) from e
        except asyncpg.exceptions.DataError as e:
            logger.error("Incorrect type inserted: %s",e)
        except asyncpg.exceptions.PostgresSyntaxError as e:
            logger.error("Missing argument exception: %s",e)


    async def _insert_user(self, user_id: int) -> None:
        """
        Async method for inserting a user into the database

        Returns
        -------
        True if insertion is successful, false otherwise
        """

        try:
            async with AsyncpgSQL(self.database_url) as conn:
                await conn.fetch(QueryString.INSERT_USER.value,user_id)
            logger.info("Inserting user successful")

        except asyncpg.exceptions.UniqueViolationError as e:
            logger.error("Duplicate key error: %s", e)
            raise DuplicateKeyError('Duplicate key for %s' % user_id) from e
        except asyncpg.exceptions.DataError as e:
            logger.error("incorrect type inserted: %s",e)
            raise TypeError('Incorrect type inserted' % e) from e


    async def _insert_batch(self,data) -> None:
        try:
            async with AsyncpgSQL(self.database_url) as conn:
                await conn.executemany(QueryString.INSERT.value,data)
            logger.info("Batch insertion successful")

        except asyncpg.exceptions.PostgresSyntaxError as e:
            logger.error("Missing argument exception: %s",e)
        except asyncpg.exceptions.ForeignKeyViolationError as e:
            logger.error('User does not exist in database: %s',e)
            raise NotFoundError('User not in database') from e
        except asyncpg.exceptions.DataError as e:
            logger.error("Incorrect type inserted: %s",e)
        except asyncpg.exceptions.UniqueViolationError as e:
            logger.error("Duplicate key error: %s",e)
            raise DuplicateKeyError('Duplicate key error, %s' % e) from e



    async def _fetch_all(self, user_id: int) -> Union[list,None]:
        """
        Async method for fetching all rows in the database

        Returns
        -------
        a list of dict
        """
        try:
            async with AsyncpgSQL(self.database_url) as conn:
                rows = await conn.fetch(QueryString.FETCH.value,user_id)
            if not rows:
                raise NotFoundError("Nothing in the Database")
            logger.info("Fetching all succeeded")
            return [{'id': row['id'],
                    'embeddings': row['embeddings'],
                    'batch_id': row['batch_id']} for row in rows]
        except asyncpg.exceptions.DataError as e:
            logger.error("Incorrect type inserted: %s",e)


    async def _update(self,
                        _id: int,
                        user_id: int,
                        embeddings: List[Union[int,float]] = None,
                        batch_id: int=None) -> None:

        try:
            async with AsyncpgSQL(self.database_url) as conn:
                if batch_id is not None and embeddings is not None:
                    await conn.execute(
                        QueryString.UPDATE_EMBS_W_BATCH.value,
                        embeddings,
                        batch_id,
                        _id,
                        user_id
                        )
                elif batch_id is not None and embeddings is None:
                    await conn.execute(
                        QueryString.UPDATE_BATCH_NO_EMBS.value,
                        batch_id,
                        _id,
                        user_id
                        )
                elif batch_id is None and embeddings is not None:
                    await conn.execute(
                        QueryString.UPDATE_NO_BATCH_W_EMBS.value,
                        embeddings,
                        _id,
                        user_id
                        )
                else:
                    await conn.execute(
                        QueryString.UPDATE_BATCH_NO_EMBS.value,
                        None,
                        _id,
                        user_id
                        )
            logger.info("Update successful")

        except asyncpg.exceptions.PostgresSyntaxError as e:
            logger.error("Missing argument exception: %s",e)
        except asyncpg.exceptions.ForeignKeyViolationError as e:
            logger.error('User does not exist in database: %s',e)
            raise NotFoundError('User not in database') from e
        except asyncpg.exceptions.DataError as e:
            logger.error("Incorrect type inserted: %s", e)
            raise TypeError('Incorrect type inserted: %s' % e) from e


    async def _delete(self, _id: int, user_id: int) -> None:
        """
        Removes a row from the database by _ID

        Returns
        -------
        None
        """

        async with AsyncpgSQL(self.database_url) as conn:
            result = await conn.fetch(QueryString.DELETE.value,_id,user_id)
        if result[0]['count'] == 0:
            raise NoUpdatesError('Nothing was changed in the database')
        logger.info("successfully deleted row")


    async def _delete_batch(self,batch_id: int,user_id: int) -> None:
        """
        Removes all rows with batch_id

        Returns
        -------
        None
        """

        async with AsyncpgSQL(self.database_url) as conn:
            result = await conn.fetch(QueryString.DELETE_BATCH.value,batch_id,user_id)
        if result[0]['count'] == 0:
            raise NoUpdatesError('Nothing was changed in the database')
        logger.info("successfully deleted row")


    async def _drop_table(self):
        """
        Method for dropping table for each setup of the server in development mode.
        """
        with open('sql/drop.sql','r') as sql_file:
            query = sql_file.read()
        try:
            conn = await asyncpg.connect(self.database_url)
            await conn.execute(query)
            logger.info("Dropped table to avoid unnecessary errors.")
        except Exception:
            logger.info("Error dropping table")
        finally:
            await conn.close()

    async def _fetch_users(self) -> Union[List[int],None]:
        """
        Async method for fetching all users in the database

        Returns
        -------
        a list of dict
        """

        try:
            async with AsyncpgSQL(self.database_url) as conn:
                rows = await conn.fetch(QueryString.FETCH_USERS.value)
            if not rows:
                raise NotFoundError("Nothing in the Database")
            logger.info("Fetching all succeeded")
            return [row['user_id'] for row in rows]
        finally:
            await conn.close()

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
        return asyncio.run(self._make_table())

    def insert(self,
                _id: int,
                user_id: int,
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

    def insert_user(self,user_id: int) -> None:
        """
        Method for inserting user into database

        Returns
        -------
        True if insertion successful, false otherwise
        """

        asyncio.run(self._insert_user(user_id=user_id))

    def fetch_all(self,user_id: int) -> Union[list,None]:
        """
        Fetches all rows in the table

        Returns
        -------
        All rows, None if a problem occurs
        """
        return asyncio.run(self._fetch_all(user_id=user_id))

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
                                user_id=user_id,
                                embeddings=embeddings,
                                batch_id=batch_id))


    def delete(self, _id: int, user_id: int) -> None:
        """
        Delete row by _id

        Returns
        -------
        Boolean, true if successful, false otherwise
        """

        asyncio.run(self._delete(_id=_id,user_id=user_id))

    def delete_batch(self, batch_id: int,user_id) -> None:
        """
        Delete row by batch_id

        Returns
        -------
        Boolean, true if successful, false otherwise
        """

        asyncio.run(self._delete_batch(batch_id=batch_id,user_id=user_id))


    def insert_batch(self, data: List[tuple]) -> None:
        """
        Method for inserting a batch of data

        Returns
        -------
        Number of inserted data
        """

        asyncio.run(self._insert_batch(data))


    def fetch_users(self) -> Union[List[int],None]:
        """
        Fetch all users in the database

        Returns
        -------
        a list of user ids
        """

        return asyncio.run(self._fetch_users())
  