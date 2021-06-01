"""
Helper classes for the app
"""
from datetime import datetime
from schema import Schema, And, Use, Optional, SchemaError,Or
from enum import Enum

class Message(Enum):
    SUCCESS="Valid input, check status for result"
    FAILURE: 'Data not in proper format, requires summary, description and structured_info with id and date(YYY-MM-DD). Summary or description may be empty strings'
    UNFILLED_REQ: 'Either summary or description must have length > 0'
        
#class BatchMessage(Enum):
    
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
                "summary": str,
                "description": str,
                "structured_info": dict
            })
        info_schema = Schema({
            "id": int,
            "issue type": Or('Bug','Epic'),
            "bucket": str,
            "date": str,
            Optional("reporter"): str,
            Optional("batchId"): str
        })
        try:
            schema.validate(data)
            info_schema.validate(data['structured_info'])
            self.validate_datestring(data['structured_info']['date'])
        except:
            raise ValueError
