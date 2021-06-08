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
            
    def validate_data(self,data: dict):
        """
        Validate whether `data` is in the enforced format.

        Returns
        -------
        None, raises ValueError if data invalid
        """
        schema = Schema({
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
    


