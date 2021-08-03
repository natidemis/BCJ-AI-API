# pylint: disable=W0703
# pylint: disable=C0103
# pylint: disable=W0622
"""
@author natidemis
June 2021

Contains the database class used for setting up for and
making query to the database
"""


import os
from typing import Union, List
from enum import Enum
from dotenv import load_dotenv
import asyncpg
from log import logger




load_dotenv()

class QueryString(Enum):
    """
    Query strings for the database
    """
    INSERT = """
    INSERT INTO Vectors(id,user_id,embeddings,batch_id)
    VALUES($1,$2,$3,$4);"""
    INSERT_USER = """
    INSERT INTO Users(user_id) VALUES($1) RETURNING *;
    """
    FETCH = "SELECT id,embeddings,batch_id FROM Vectors WHERE user_id = $1;"
    FETCH_USERS = "SELECT user_id from Users;"
    DELETE = """
    WITH deleted AS (
        DELETE FROM Vectors 
        WHERE id = $1 AND user_id = $2 RETURNING *
        )
    SELECT count(*) 
    FROM deleted;"""
    UPDATE_EMBS_W_BATCH = """
    UPDATE Vectors
    SET embeddings = $1,
    batch_id = $2
    WHERE id = $3 AND user_id = $4 RETURNING * ;
    """
    UPDATE_BATCH_NO_EMBS = """
    UPDATE Vectors
    SET batch_id = $1
    WHERE id = $2 AND user_id = $3 RETURNING *;
    """
    UPDATE_NO_BATCH_W_EMBS = """
    UPDATE Vectors
    SET embeddings = $1
    WHERE id = $2 AND user_id = $3 RETURNING *;
    """

    DELETE_BATCH = """
    WITH deleted AS (
        DELETE FROM Vectors 
        WHERE batch_id = $1 AND user_id = $2 RETURNING *
        )
    SELECT count(*) 
    FROM deleted;"""

    GET_BATCH_BY_ID = """
    SELECT * FROM Vectors
    WHERE batch_id = $1;
    """

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


class Database:
    """
    Class for handling database connection and queries

    Class methods:
    connect_pool

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
    def __init__(self, pool):
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
        self.pool = pool

    @classmethod
    async def connect_pool(cls):
        """
        Creates a pool for the database. Database must be initalized using
        this class method.
        """
        pool = await asyncpg.create_pool(os.getenv('DATABASE_URL'), command_timeout=60)
        return cls(pool=pool)

    async def setup_database(self, reset: bool = False) -> bool:
        """
        Instance method to create the table

        Arguments
        ---------
        None

        Returns
        -------
        True if table creation successful, false otherwise
        """
        if reset:
            with open('sql/drop.sql','r') as sql_file:
                query = sql_file.read()
            async with self.pool.acquire() as conn:
                try:
                    await conn.execute(query)
                    logger.info("Dropped table to avoid unnecessary errors.")
                except Exception:
                    logger.info("Error dropping table")

        with open('sql/schema.sql','r') as sql_file:
            query = sql_file.read()

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query)
                logger.info("Checking and/or setting up database complete.")
            return True
        except RuntimeError:
            logger.error("Setting up database failed, re-evaluate enviroment variables.")
            return False


    async def insert(self,
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
        try:
            async with self.pool.acquire() as conn:
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


    async def insert_user(self, user_id: int) -> None:
        """
        Instance method for inserting a user into the database

        Arguments
        ---------
        user_id: int
            identification number for user.

        Returns
        -------
        True if insertion is successful, false otherwise
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(QueryString.INSERT_USER.value,user_id)
        except asyncpg.exceptions.UniqueViolationError as e:
            logger.error("Duplicate key error: %s", e)
            raise DuplicateKeyError('Duplicate key for %s' % user_id,user_id) from e
        except asyncpg.exceptions.DataError as e:
            logger.error("incorrect type inserted: %s",e)
            raise TypeError('Incorrect type inserted' % e) from e


    async def insert_batch(self,data: List[tuple]) -> None:
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
        try:
            async with self.pool.acquire() as conn:
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



    async def fetch_all(self, user_id: int) -> Union[list,None]:
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
        try:
            async with self.pool.acquire() as conn:
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

    async def update(self,
                        id: int,
                        user_id: int,
                        embeddings: List[Union[int,float]] = None,
                        batch_id: int=None) -> None:
        """
        Instance method for updating a bug for a user.

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
            async with self.pool.acquire() as conn:
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


    async def delete(self, id: int, user_id: int) -> None:
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

        async with self.pool.acquire() as conn:
            result = await conn.fetch(QueryString.DELETE.value,id,user_id)
            if result[0]['count'] == 0:
                raise NoUpdatesError('Nothing was changed in the database',(id,user_id))



    async def delete_batch(self,batch_id: int,user_id: int) -> None:
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

        async with self.pool.acquire() as conn:
            result = await conn.fetch(QueryString.DELETE_BATCH.value,batch_id,user_id)
            if result[0]['count'] == 0:
                raise NoUpdatesError('Nothing was changed in the database',(batch_id,user_id))



    async def fetch_users(self) -> Union[List[int],None]:
        """
        Instance method for fetching all users in the database

        Arguments
        ---------
        None

        Returns
        -------
        a list of ids, raises NotFoundError if no users exist in the database
        """


        async with self.pool.acquire() as conn:
            rows = await conn.fetch(QueryString.FETCH_USERS.value)
            if not rows:
                raise NotFoundError("Nothing in the Database")
            logger.info("Fetching all succeeded")
            return [row['user_id'] for row in rows]
