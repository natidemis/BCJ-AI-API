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

#Uncomment this line to run on windows

#asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class NotFoundError(Exception):
    """
    Database error when return value is empty.
    """
    def __init__(self, message: str, *args):
        super().__init__(message, *args)
        self.message = message
        self.args = args

    def __str__(self):
        return "{}: {}".format(self.message,self.args)

class DuplicateKeyError(Exception):
    """
    Database error to raise when the key inserted already exists.
    """
    def __init__(self,message, *args):
        super().__init__(message, *args)
        self.message = message
        self.args = args

    def __str__(self):
        return "{}: {}".format(self.message,self.args)


class NoUpdatesError(Exception):
    """
    Database error when a query makes no changes to the database.
    """
    def __init__(self,message, *args):
        super().__init__(message, *args)
        self.message = message
        self.args = args

    def __str__(self):
        return "{}: {}".format(self.message,self.args)



class AsyncpgSQL():
    """
    Context manager for asyncpg
    """
    def __init__(self, url):
        self._url = url
        self._conn = None

    async def __aenter__(self):
        """
        Connects the database
        """
        self._conn = await asyncpg.connect(self._url)
        return self._conn

    async def __aexit__(self, exc_type, exc, tb): #closing the connection
        """
        Closes the database connection
        """
        if self._conn:
            await self._conn.close()

class Database:
    """
    Class for handling database connection and queries

    Class methods:
    _make_table
    _insert
    _insert_user
    _insert_batch
    _fetch_all
    _update
    _delete
    _delete_batch
    _fetch_users
    _drop_table

    Instance methods:
    make_table
    insert
    insert_user
    insert_batch
    fetch_all
    update
    delete
    delete_batch
    fetch_users
    drop_table

    Instance variables:
    database_url
    """
    def __init__(self):
        """
        Initialize Database

        Requirements:
            - DATABASE_URL variable in '.env' file.

        Arguments
        ---------
        None

        Returns
        -------
        Instance of a Database object
        """
        self.database_url = os.getenv('DATABASE_URL')



    async def _make_table(self) -> bool:
        """
        Class method to create the table

        Arguments
        ---------
        None

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
                        id: int,
                        user_id: int,
                        embeddings: List[Union[int,float]],
                        batch_id: int= None) -> None:
        """
        Class method for inserting into the database

        Arguments
        ---------
        id: int
            Identification number for the embedded bug

        user_id: int
            Indentification number of the user

        embeddings: Array of floats
            The embeddings of the bug

        Batch_id: int, None
            Batch ID to associate bug with a batch of bugs

        Returns
        -------
        None, raises DuplicateKeyError, NotFoundError on exception
        """

        try:
            async with AsyncpgSQL(self.database_url) as conn:
                await conn.execute(QueryString.INSERT.value,id,user_id,embeddings,batch_id)

        except asyncpg.exceptions.UniqueViolationError as e:
            logger.error("Duplicate key error: %s for user_id: %s and id: %s",e,user_id,id)
            raise DuplicateKeyError('Duplicate key error: %s' % e,(id,user_id)) from e
        except asyncpg.exceptions.ForeignKeyViolationError as e:
            logger.error('User_id does not exist in the Users database: %s,'
             'exception: %s',user_id,e)
            raise NotFoundError('122 User not in database: %s' % e,(id,user_id)) from e
        except asyncpg.exceptions.DataError as e:
            logger.error("Incorrect type inserted: %s",e)
        except asyncpg.exceptions.PostgresSyntaxError as e:
            logger.error("Missing argument exception: %s",e)


    async def _insert_user(self, user_id: int) -> None:
        """
        Class method for inserting a user into the database

        Arguments
        ---------
        user_id: int
            identification number for user.

        Returns
        -------
        True if insertion is successful, false otherwise
        """

        try:
            async with AsyncpgSQL(self.database_url) as conn:
                await conn.execute(QueryString.INSERT_USER.value,user_id)

        except asyncpg.exceptions.UniqueViolationError as e:
            logger.error("Duplicate key error: %s", e)
            raise DuplicateKeyError('Duplicate key for %s' % user_id,user_id) from e
        except asyncpg.exceptions.DataError as e:
            logger.error("incorrect type inserted: %s",e)
            raise TypeError('Incorrect type inserted' % e) from e


    async def _insert_batch(self,data: List[tuple]) -> None:
        """
        Class method for inserting a batch of data

        Arguments
        ---------
        data: List of tuples [(id, user_id, embeddings, batch_id)]
            id: int - Identification value for the bug.
            user_id: int - Identification value for the user.
            embeddings: List of floats - The embeddings for this bug
            batch_id: int | None - A batch number to associate this bug with other bugs.

        Returns
        -------
        None, raises NotFoundError, Duplicate Error on exception
        """
        try:
            async with AsyncpgSQL(self.database_url) as conn:
                await conn.executemany(QueryString.INSERT.value,data)

        except asyncpg.exceptions.ForeignKeyViolationError as e:
            logger.error('User does not exist in database: %s',e)
            raise NotFoundError('User not in database') from e
        except asyncpg.exceptions.DataError as e:
            logger.error("Incorrect type inserted: %s",e)
            raise NotFoundError('Incorrect type input' % e) from e
        except asyncpg.exceptions.UniqueViolationError as e:
            logger.error("Duplicate key error: %s",e)
            raise DuplicateKeyError('Duplicate key error, %s' % e) from e



    async def _fetch_all(self, user_id: int) -> Union[list,None]:
        """
        Class method for fetching all rows for a user in the database

        Arguments
        ---------
        user_id: int
            User identification number

        Returns
        -------
        a list of dict, Raises NotFoundError is user has no rows to fetch.
        """
        try:
            async with AsyncpgSQL(self.database_url) as conn:
                rows = await conn.fetch(QueryString.FETCH.value,user_id)
                if not rows:
                    raise NotFoundError("Nothing in the Database",rows)
            logger.info("Fetching all succeeded")
            return [{'id': row['id'],
                    'embeddings': row['embeddings'],
                    'batch_id': row['batch_id']} for row in rows]
        except asyncpg.exceptions.DataError as e:
            logger.error("Incorrect type inserted: %s",e)
            return None

    async def _update(self,
                        id: int,
                        user_id: int,
                        embeddings: List[Union[int,float]] = None,
                        batch_id: int=None) -> None:
        """
        Class method for updating a bug for a user.

        Arguments
        ---------
        id: int
            Identification number for the embedded bug

        user_id: int
            Indentification number of the user

        embeddings: Array of floats | None
            The embeddings of the bug

        Batch_id: int | None
            Batch ID to associate bug with a batch of bugs

        Returns
        None, raises NoUpdatesError if nothing is updated.
        """
        try:
            async with AsyncpgSQL(self.database_url) as conn:
                if batch_id is not None and embeddings is not None:
                    result = await conn.execute(
                        QueryString.UPDATE_EMBS_W_BATCH.value,
                        embeddings,
                        batch_id,
                        id,
                        user_id
                        )
                elif batch_id is not None and embeddings is None:
                    result = await conn.execute(
                        QueryString.UPDATE_BATCH_NO_EMBS.value,
                        batch_id,
                        id,
                        user_id
                        )
                elif batch_id is None and embeddings is not None:
                    result = await conn.execute(
                        QueryString.UPDATE_NO_BATCH_W_EMBS.value,
                        embeddings,
                        id,
                        user_id
                        )
                else:
                    result = await conn.execute(
                        QueryString.UPDATE_BATCH_NO_EMBS.value,
                        None,
                        id,
                        user_id
                        )
                if result == 'UPDATE 0':
                    raise NoUpdatesError('No changes were made to the db',(id,user_id,batch_id))
                logger.info("Update successful")

        except asyncpg.exceptions.PostgresSyntaxError as e:
            logger.error("Missing argument exception: %s",e)
        except asyncpg.exceptions.DataError as e:
            logger.error("Incorrect type inserted: %s", e)


    async def _delete(self, id: int, user_id: int) -> None:
        """
        Class method for removing a row from the database

        Arguments
        ---------
        id: int
            Id of the bug

        user_id: int
            User identification number

        Returns
        -------
        None, raises NoUpdatesError if no deletion occurs.
        """

        async with AsyncpgSQL(self.database_url) as conn:
            result = await conn.fetch(QueryString.DELETE.value,id,user_id)
            if result[0]['count'] == 0:
                raise NoUpdatesError('Nothing was changed in the database',(id,user_id))



    async def _delete_batch(self,batch_id: int,user_id: int) -> None:
        """
        Class method for removing a batch of rows

        Arguments
        ---------
        batch_id: int
            Indentification number for a set of bugs

        user_id: int
            User identification number assosicated with this batch

        Returns
        -------
        None, raises NoUpdatesError if no deletes occur
        """

        async with AsyncpgSQL(self.database_url) as conn:
            result = await conn.fetch(QueryString.DELETE_BATCH.value,batch_id,user_id)
            if result[0]['count'] == 0:
                raise NoUpdatesError('Nothing was changed in the database',(batch_id,user_id))



    async def _drop_table(self):
        """
        Class method for dropping table. Used in development

        """
        with open('sql/drop.sql','r') as sql_file:
            query = sql_file.read()
        async with AsyncpgSQL(self.database_url) as conn:
            try:
                conn = await asyncpg.connect(self.database_url)
                await conn.execute(query)
                logger.info("Dropped table to avoid unnecessary errors.")
            except Exception:
                logger.info("Error dropping table")

    async def _fetch_users(self) -> Union[List[int],None]:
        """
        Class method for fetching all users in the database

        Arguments
        ---------
        None

        Returns
        -------
        a list of ids, raises NotFoundError if no users exist in the database
        """


        async with AsyncpgSQL(self.database_url) as conn:
            rows = await conn.fetch(QueryString.FETCH_USERS.value)
            if not rows:
                raise NotFoundError("Nothing in the Database")
            logger.info("Fetching all succeeded")
            return [row['user_id'] for row in rows]


    def drop_table(self):
        """
        Method for dropping the table

        **MAKE SURE YOU'RE IN DEVELOPMENT CODE WHEN RUNNING TESTS
        AND RUNNING THIS FUNCTION IN GENERAL**

        When setting up for production, set ENVIROMENT = production
        in '.env'
        """
        if os.getenv('ENVIROMENT') is not None \
            and os.getenv('ENVIROMENT') == 'production':
            return
        asyncio.run(self._drop_table())


    def make_table(self) -> bool:
        """
        Instance method to create the table

        Arguments
        ---------
        None

        Returns
        -------
        True if table creation successful, false otherwise
        """
        return asyncio.run(self._make_table())

    def insert(self,
                id: int,
                user_id: int,
                embeddings: List[Union[int,float]],
                batch_id: int= None) -> None:
        """
        Instance method for inserting into the database

        Arguments
        ---------
        id: int
            Identification number for the embedded bug

        user_id: int
            Indentification number of the user

        embeddings: Array of floats
            The embeddings of the bug

        Batch_id: int, None
            Batch ID to associate bug with a batch of bugs

        Returns
        -------
        None, raises DuplicateKeyError, NotFoundError on exception
        """

        asyncio.run(self._insert(
                                id=id,
                                user_id = user_id,
                                embeddings=embeddings,
                                batch_id=batch_id))

    def insert_user(self,user_id: int) -> None:
        """
        Class method for inserting a user into the database

        Arguments
        ---------
        user_id: int
            identification number for user.

        Returns
        -------
        True if insertion is successful, false otherwise
        """

        asyncio.run(self._insert_user(user_id=user_id))

    def fetch_all(self,user_id: int) -> Union[list,None]:
        """
        Instance method for fetching all rows for a user in the database

        Arguments
        ---------
        user_id: int
            User identification number

        Returns
        -------
        a list of dict, Raises NotFoundError is user has no rows to fetch.
        """
        return asyncio.run(self._fetch_all(user_id=user_id))

    def update(self,
                id: int,
                user_id: int,
                embeddings: List[Union[int,float]] = None,
                batch_id: int=None) -> None:
        """
        Class method for updating a bug for a user.

        Arguments
        ---------
        id: int
            Identification number for the embedded bug

        user_id: int
            Indentification number of the user

        embeddings: Array of floats | None
            The embeddings of the bug

        Batch_id: int | None
            Batch ID to associate bug with a batch of bugs

        Returns
        None, raises NoUpdatesError if nothing is updated.
        """
        asyncio.run(self._update(
                                id=id,
                                user_id=user_id,
                                embeddings=embeddings,
                                batch_id=batch_id))


    def delete(self, id: int, user_id: int) -> None:
        """
        Instance method for removing a row from the database

        Arguments
        ---------
        id: int
            Id of the bug

        user_id: int
            User identification number

        Returns
        -------
        None, raises NoUpdatesError if no deletion occurs.
        """

        asyncio.run(self._delete(id=id,user_id=user_id))

    def delete_batch(self, batch_id: int,user_id) -> None:
        """
        Instance method for removing a batch of rows

        Arguments
        ---------
        batch_id: int
            Indentification number for a set of bugs

        user_id: int
            User identification number assosicated with this batch

        Returns
        -------
        None, raises NoUpdatesError if no deletes occur
        """

        asyncio.run(self._delete_batch(batch_id=batch_id,user_id=user_id))


    def insert_batch(self, data: List[tuple]) -> None:
        """
        Instance method for inserting a batch of data

        Arguments
        ---------
        data: List of tuples [(id, user_id, embeddings, batch_id)]
            id: int - Identification value for the bug.
            user_id: int - Identification value for the user.
            embeddings: List of floats - The embeddings for this bug
            batch_id: int | None - A batch number to associate this bug with other bugs.

        Returns
        -------
        None, raises NotFoundError, Duplicate Error on exception
        """

        asyncio.run(self._insert_batch(data))


    def fetch_users(self) -> Union[List[int],None]:
        """
        Instance method for fetching all users in the database

        Arguments
        ---------
        None

        Returns
        -------
        a list of ids, raises NotFoundError if no users exist in the database
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._fetch_users())

  