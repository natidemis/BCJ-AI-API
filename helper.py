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
from flask import jsonify, make_response

class QueryString(Enum):
    INSERT = """
    INSERT INTO Vectors(id,summary,descr,bucket,dateUP)
    VALUES($1,$2,$3,$4,$5); """
    FETCH = "SELECT * FROM Vectors;"
    DELETE = "DELTE FROM Vectors WHERE id = $1"
    UPDATE_DESCR_NO_BUCKET = """
    UPDATE Vectors 
    SET descr = $1,
    dateUP = $2
    WHERE id = $3;"""
    UPDATE_DESCR_W_BUCKET = """
    UPDATE Vectors
    SET descr = $1,
    bucket = $2,
    dateUP = $3,
    WHERE id = $4;"""

    UPDATE_SUMM_NO_BUCKET = """
    UPDATE Vectors
    SET summary = $1,
    dateUP = $2
    WHERE id = $3; """

    UPDATE_SUMM_W_BUCKET ="""
    UPDATE Vectors
    SET summary = $1,
    bucket = $2,
    dateUP = $3
    WHERE id = $4; """
    UPDATE_SUMM_AND_DESCR_NO_BUCKET = """
    UPDATE Vectors
    SET summary = $1,
    descr = $2,
    dateUP = $3
    WHERE id = $4; """
    
    UPDATE_SUMM_AND_DESCR_W_BUCKET = """
    UPDATE Vectors
    SET summary = $1,
    descr = $2,
    bucket = $3,
    dateUP = $4
    WHERE id = $5; """
    UPDATE_BUCKET_ONLY = """
    UPDATE Vectors
    SET bucket = $1
    WHERE id = $2; """

class Message(Enum):
    VALID_INPUT = 'Valid input, check status for result'
    FAILURE = 'Data not in proper format, read the requirements here: -----'
    UNFULFILLED_REQ = 'Either summary or description must have length > 0'
    UNAUTHORIZED = 'Unauthorized, wrong token'
    REMOVED = 'Successfully removed'
    INVALID = 'Invalid ID'
    
class Validator:

    def __init__(self):
        """
        A class containing validation functions for the app
        """
        
    def validate_datestring(self, date: str) -> None:
        """
        Verify that `date` is in YYYY-MM-DD format

        Returns
        -------
        None, raises value error if 'date' is invalid
        """
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except:
            raise ValueError
    
    def validate_update_data(self, data: dict) -> None:
        """
        Validate whether the required variables are there to update

        Returns
        -------
        None, raises ValueError if data is not in proper format
        """
        schema = Schmea({
            Optional("summary"): str,
            Optional("description"): str,
            'structured_info': dict
        })
        info_schema = Schema({
            'id': Or(str, int),
            'date': str,
            Optional("bucket"): str
        })

        try:
            schema.validate(data)
            info_schema.validate(data['structured_info'])
            self.validate_datestring(data['structured_info']['date'])
        except(ValueError):
            raise ValueError

    def validate_data(self,data: dict) -> None:
        """
        Validate whether `data` is in the enforced format.

        Returns
        -------
        None, raises ValueError if data is not in proper format
        """
        schema = Schema({
                "summary": str,
                "description": str,
                "structured_info": dict,
                Optional("k"): And(int, lambda n: n>0)
            })
        info_schema = Schema({
            "id": Or(str, int),
            Optional("bucket"): str,
            "date": str
        })
        try:
            schema.validate(data)
            info_schema.validate(data['structured_info'])
            self.validate_datestring(data['structured_info']['date'])
        except(ValueError):
            raise ValueError
         
    def validate_id(self, data: dict) -> None:
        """
        Validate whether `data` is in the enforced format.

        Returns
        -------
        None, raises ValueError if `data` invalid
        """
        schema = Schema({
            "id": int #Bug id's are strings while batch id's are integers
        })
        try:
            schema.validate(data)
        except:
            raise ValueError
    


