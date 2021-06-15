from dotenv import load_dotenv
import asyncpg
import asyncio
import os
import dotenv

load_dotenv()


class Database:
    CREATED = False
    HOST = os.getenv('DB_HOST')
    NAME = os.getenv('DB_NAME')
    USER = os.getenv('DB_USER')
    PASSWORD = os.getenv('DB_PASSWORD')
 
    def __init__(self):
        """
        Class to setup the database table when required.
        """
    
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
            return True
        except:
            return False


    async def __insert(self, id: int, vec: list, bucket: str) -> bool:
        """
        Async method for inserting into the database

        Returns
        -------
        True if insertion is successful, false otherwise
        """
        sql_file = open('sql/insert.sql','r')
        query = sql_file.read()
        sql_file.close()
        try:
            conn = await asyncpg.connect('postgres://{}:{}@{}/{}'.format(self.USER,self.PASSWORD,self.HOST,self.NAME))
            await conn.execute(query,id,vec,bucket)
            await conn.close()
            return True
        except:
            return False
    
    async def __fetch_all(self) -> list:
        """
        Async method for fetching all rows in the database

        Returns
        -------
        a list of dict
        """
        sql_file = open('sql/fetch.sql','r')
        query = sql_file.read()
        sql_file.close()
        try:
            conn = await asyncpg.connect('postgres://{}:{}@{}/{}'.format(self.USER,self.PASSWORD,self.HOST,self.NAME))
            rows = await conn.fetch(query)
            await conn.close()
            return [{'id': row['id'],'vector': row['vector'],'bucket': row['bucket']} for row in rows]
        except:
            return None

    def make_table(self) -> bool:
        """
        One time use to set up the Vectors table, 
        required to determine vector length.

        Returns
        -------
        True if table creation is successful, false otherwise
        """

        return asyncio.run(self.__make_table())

    def insert(self,id: int,vec: list, bucket: str) -> bool:
        """
        Method for inserting into the database

        Returns
        -------
        True if insertion successful, false otherwise
        """
        return asyncio.run(self.__insert(id=id,vec=vec,bucket=bucket))
    
    def fetch_all(self) -> list:
        """
        Fetches all rows in the table

        Returns
        -------
        All rows, None if a problem occurs
        """
        return asyncio.run(self.__fetch_all())