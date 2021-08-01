from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, validator, Extra

"""
@authors: Gitcelo, natidemis
May-June 2021

Datastructures for input requests
"""

class StructuredInfoBaseModel(BaseModel, extra=Extra.forbid):
    """
    Base Model for all 'structured_info' variables
    """
    date: str

    @validator('date', pre= True)
    def parse_date(cls, value: str) -> None: #pylint: disable=E0213
        """
        Verify that `date` is in YYYY-MM-DD format

        Arguments
        ---------
            date: str
                date string to be validated.

        Returns
        -------
        'v', raises ValueError if 'date' is invalid
        """
        try:
            datetime.strptime(value, '%Y-%m-%d')
        except (TypeError, ValueError) as exp:
            raise ValueError('Not in correct format') from exp
        return value

class StructuredInfoMainModel(StructuredInfoBaseModel):
    """
    'structured_info' validator for patch and post on '/bug'
    """
    id: int
    batch_id: Optional[str] = None

class StructuredInfoBatchModel(StructuredInfoBaseModel):
    """
    'structured_info' validator for 'post' og '/batch'
    """
    id: int
    batch_id: int



class BaseDataModel(BaseModel,extra=Extra.forbid):
    """
        Base model for all validators
    """
    user_id: int
    summary: Optional[str] = None
    description: Optional[str] = None
    structured_info: StructuredInfoBaseModel

    def __init_subclass__(cls, optional_fields=None, **kwargs):
        """
        allow some fields of subclass turn into optional
        """
        super().__init_subclass__(**kwargs)
        if optional_fields:
            for field in optional_fields:
                cls.__fields__[field].outer_type_ = Optional
                cls.__fields__[field].required = False


class MainDataModel(BaseDataModel):
    """
     Validator for patch and post on '/bug'
    """

    structured_info: StructuredInfoMainModel



class GetDataModel(BaseDataModel):
    """
    Validator for /get on '/bug'
    """
    k: Optional[int] = 5

    @validator('k', pre= True)
    def validate_k(cls,value) -> int: #pylint: disable=E0213
        """
        Validates 'value' > 0
        """
        if value is not None:
            assert value > 0, '"k" must meet the constraint k > 0'
        return value

class ValidBatchModel(BaseModel):
    """
    Validator list data on 'post' on '/batch'
    """
    summary: Optional[str] = None
    description: Optional[str] = None
    structured_info: StructuredInfoBatchModel



class BatchDataModel(BaseModel):
    """
    Validator for 'post' on '/batch'
    """
    user_id: int
    data: List[ValidBatchModel]

class DeleteDataModel(BaseModel):
    """
    Validator for 'delete' on '/bug'
    """
    user_id: int
    id: int

class DeleteBatchDataModel(BaseModel):
    """
    Validator for 'delete' on '/batch'
    """
    user_id: int
    batch_id: int