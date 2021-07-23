# pylint: disable=R0201
# pylint: disable=C0301
"""
@author natidemis
June 2021

Helper classes for the app
"""

from datetime import datetime
from enum import Enum
from schema import Schema, And, Optional, Or


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
    WHERE id = $2 AND user_id = $3 RETRUNING *;
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

class Message(Enum):
    """
    Messages for response to http requests
    """
    VALID_INPUT = 'Valid input, check status for result'
    FAILURE = '''Data not in proper format, read the requirement on github: https://github.com/natidemis/BCJ-AI-API'''
    UNFULFILLED_REQ = 'Either summary or description must have length > 0'
    UNAUTHORIZED = 'Unauthorized, wrong token'
    REMOVED = 'Successfully removed'
    INVALID = 'Invalid ID'
    INVALID_ID_OR_DATE = ("Either the id already exists or "
                "the given date is not valid")
    NO_USER = "User not available."
class Validator:
    """
    Miscellaneous class for all things validation for the app.
    """

    def __init__(self):
        """
        A class containing validation functions for the app
        """
        self.info_schema = Schema({
            'id': int,
            'date': str,
            Optional("batch_id"): int
        })
        self.batch_schema = Schema({
            'id': int,
            'date': str,
            'batch_id': int
        })
        self.info_schema_get = Schema({
            'date': str,
        })
        self.info_schema_update = Schema({
            'id': int,
            'date': str,
            Optional("batch_id"): Or(int,None)
        })


    @staticmethod
    def validate_datestring( date: str) -> None:
        """
        Verify that `date` is in YYYY-MM-DD format

        Returns
        -------
        None, raises value error if 'date' is invalid
        """
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except:
            raise ValueError from Exception

    def validate_update_data(self, data: dict) -> None:
        """
        Validate whether the required variables are there to update

        Returns
        -------
        None, raises SchemaError if data is not in proper format
        """
        schema = Schema({
            "user_id": int,
            Optional("summary"): str,
            Optional("description"): str,
            'structured_info': dict
        })

        try:
            schema.validate(data)
            self.info_schema_update.validate(data['structured_info'])
            self.validate_datestring(data['structured_info']['date'])
        except:
            raise ValueError from Exception

    def validate_data(self,data: dict) -> None:
        """
        Validate whether `data` is in the enforced format.

        Returns
        -------
        None, raises SchemaError if data is not in proper format
        """
        schema = Schema({
                "user_id": int,
                "summary": str,
                "description": str,
                "structured_info": dict,
                Optional("k"): And(int, lambda n: n>0)
            })

        try:
            schema.validate(data)
            self.info_schema.validate(data['structured_info'])
            self.validate_datestring(data['structured_info']['date'])
        except:
            raise ValueError from Exception

    def validate_data_get(self,data: dict) -> None:
        """
        Validate whether `data` is in the enforced format.
        Used for the get request on /bug

        Returns
        -------
        None, raises SchemaError if data is not in proper format
        """
        schema = Schema({
                "user_id": int,
                "summary": str,
                "description": str,
                'structured_info': dict,
                Optional("k"): And(int, lambda n: n>0)
            })

        try:
            schema.validate(data)
            self.info_schema_get.validate(data['structured_info'])
            self.validate_datestring(data['structured_info']['date'])
        except:
            raise ValueError from Exception

    def validate_batch_data(self,data: dict) -> None:
        """
        Validate whether `data` is in the enforced format.

        Returns
        -------
        None, raises SchemaError if data is not in proper format
        """
        schema = Schema(
            {
                "summary": str,
                "description": str,
                "structured_info": dict,
            }
        )

        try:
            schema.validate(data)
            self.batch_schema.validate(data['structured_info'])
            self.validate_datestring(data['structured_info']['date'])
        except:
            raise ValueError from Exception

    def validate_id(self, data: dict) -> None:
        """
        Validate whether `data` is in the enforced format.
        Helper function for 'delete' og '/bug'
        Returns
        -------
        None, raises SchemaError if `data` invalid
        """
        schema = Schema({
            "user_id": int,
            "id": int #Bug id's are strings while batch id's are integers
        })
        try:
            schema.validate(data)
        except:
            raise ValueError from Exception

    def validate_batch_id(self, data: dict) -> None:
        """
        Validate whether `data` is in the enforced format.

        Returns
        -------
        None, raises SchemaError if `data` invalid
        """
        schema = Schema({
            "user_id": int,
            "batch_id": int #Bug id's are strings while batch id's are integers
        })
        try:
            schema.validate(data)
        except:
            raise ValueError from Exception
