"""
@author natidemis
June 2021

Helper classes for the app
"""

"""
TODO

Bæta við hlekk í FAILURE skilaboðin
"""
from datetime import datetime
from schema import Schema, And, Use, Optional, SchemaError,Or
from enum import Enum
from config import SECRET_TOKEN
from flask import jsonify, make_response
from dotenv import load_dotenv
import psycopg2
import os
import dotenv

class Message(Enum):
    VALID_INPUT = 'Valid input, check status for result'
    FAILURE = 'Data not in proper format, read the requirements here: -----'
    UNFULFILLED_REQ = 'Either summary or description must have length > 0'
    UNAUTHORIZED = 'Unauthorized, wrong token'
    REMOVED = 'Successfully removed'
    INVALID = 'Invalid ID'
    
class Helper:

    def __init__(self):
        """
        A class containing validation functions for the app
        """
        
    def validate_datestring(self, stringdate):
        try:
            datetime.strptime(stringdate, '%Y-%m-%d')
        except:
            raise ValueError
            
    def validate_data(self,data):
        schema = Schema({
                "token": str,
                "summary": str,
                "description": str,
                "structured_info": dict,
                Optional("k"): And(int, lambda n: n>0)
            })
        info_schema = Schema({
            "id": Or(str, int),
            "bucket": str,
            "date": str,
            Optional("reporter"): str
        })
        try:
            schema.validate(data)
            info_schema.validate(data['structured_info'])
            self.validate_datestring(data['structured_info']['date'])
        except(ValueError):
            raise ValueError
         
    def validate_id(self, data):
        schema = Schema({
            "token": str,
            "id": int #Bug id's are strings while batch id's are integers
        })
        try:
            schema.validate(data)
        except:
            raise ValueError
    
    def auth_token(self,token):
        return token == SECRET_TOKEN


class Database_setup:
    load_dotenv()
    CREATED = False
    HOST = os.getenv('DB_HOST')
    NAME = os.getenv('DB_NAME')
    USER = os.getenv('DB_USER')
    PASSWORD = os.getenv('DB_PASSWORD')
    def __init__(self):
        """
        Class to setup the database table when required.
        """
    
    def make_table(self, size: int):
        """
        One time use to set up the Vectors table, 
        required to determine vector length.
        """
        if self.CREATED:
            return
        sql_file = open('sql/schema.sql','r')
        schema = sql_file.read()
        sql_file.close()
        conn = psycopg2.connect(dbname=self.NAME,user=self.USER, password=self.PASSWORD, host=self.HOST)
        cur = conn.cursor()
        cur.execute(schema,[size])
        conn.commit()
        cur.close()
        
        conn.close()
        self.CREATED = True