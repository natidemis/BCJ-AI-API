# pylint: disable=R0201
# pylint: disable=E0611
# pylint: disable=R0903
# pylint: disable=W0707
"""
@authors: Gitcelo, natidemis
May-June 2021

API for AI web service
"""

import os
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel, validator, Extra
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from bcj_ai import BCJAIapi as ai
from helper import Message



load_dotenv()
secret_token = os.getenv('SECRET_TOKEN')
app = FastAPI()

#validator = Validator()
ai = ai()


# TODO: Set Limit on summary and description #pylint: disable=W0511
# TODO: take in command-line-argument to reset the database.
# TODO: make fetch_vectors and gen_token a setup.py file. 
# TODO: movie base classes to a separate file
def verify_token(req: Request):
    """
    Authentication method for the enviroment using this service
    via SECRET_TOKEN
    """
    if 'authorization' in req.headers and \
        req.headers['authorization'].split(' ')[1] == secret_token:
        return True

    raise HTTPException(
            status_code= 401,
            detail='Unauthorized'
        )

class StructuredInfoBase(BaseModel, extra=Extra.forbid):
    """
    Base Model for all 'structured_info' variables
    """
    date: str

    #class Config:
    #    """
    #    Settings for the class
    #    """
    #    extra: Extra.forbid
    #    validate_assignment: True

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

class StructuredInfoMain(StructuredInfoBase):
    """
    'structured_info' validator for patch and post on '/bug'
    """
    id: int
    batch_id: Optional[str] = None

class StructuredInfoBatch(StructuredInfoBase):
    """
    'structured_info' validator for 'post' og '/batch'
    """
    id: int
    batch_id: int



class BaseData(BaseModel,extra=Extra.forbid):
    """
        Base model for all validators
    """
    user_id: int
    summary: Optional[str] = None
    description: Optional[str] = None
    structured_info: StructuredInfoBase

    def __init_subclass__(cls, optional_fields=None, **kwargs):
        """
        allow some fields of subclass turn into optional
        """
        super().__init_subclass__(**kwargs)
        if optional_fields:
            for field in optional_fields:
                cls.__fields__[field].outer_type_ = Optional
                cls.__fields__[field].required = False


    #class Config:
    #    """
    #    Settings for the class
    #    """
    #    extra: Extra.forbid
    #    validate_assignment: True

class MainData(BaseData):
    """
     Validator for patch and post on '/bug'
    """

    structured_info: StructuredInfoMain



class GetData(BaseData):
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

class ValidBatch(BaseModel):
    """
    Validator list data on 'post' on '/batch'
    """
    summary: Optional[str] = None
    description: Optional[str] = None
    structured_info: StructuredInfoBatch



class BatchData(BaseModel):
    """
    Validator for 'post' on '/batch'
    """
    user_id: int
    data: List[ValidBatch]

class DeleteData(BaseModel):
    """
    Validator for 'delete' on '/bug'
    """
    user_id: int
    id: int

class DeleteBatchData(BaseModel):
    """
    Validator for 'delete' on '/batch'
    """
    user_id: int
    batch_id: int

@app.get('/bug', status_code=200)
async def k_most_similar_bugs(data: GetData, authorized: bool = Depends(verify_token)):
    """
    GET method that fetches the k UPs that are most similar to the UP
    Returns
    -------
    ID's of the k most similar UPs if everything went well, else an error message
    Status code
    """

    if authorized:
        try:
            bugs = await ai.get_similar_bugs_k(**data.dict())
        except ValueError :
            raise HTTPException(status_code=404, detail=Message.NO_USER.value)
        except AssertionError:
            raise HTTPException(status_code=400,detail=Message.UNFULFILLED_REQ.value)
        return JSONResponse(content=bugs[1], status_code=bugs[0].value)
    return JSONResponse(content={'Unauthorized'}, status_code=401)



@app.post('/bug', status_code=200)
async def insert_bugs(data: MainData, authorized: bool = Depends(verify_token)):
    """
    Method for handling POST request on '/bug',
    used for inserting a UP to the AI and its database.
    Returns
    -------
    A message with a brief description explaining the result for the request and status code.
    """

    if authorized:
        try:
            status, message = await ai.add_bug(**data.dict())
        except ValueError:
            raise HTTPException(status_code=404, detail= Message.NO_USER.value)
        except AssertionError:
            raise HTTPException(status_code=404, detail= Message.UNFULFILLED_REQ.value)

        return JSONResponse(content={'detail': message.value}, status_code=status.value)

    return JSONResponse(content={'Unauthorized'}, status_code=401)
@app.patch('/bug', status_code= 200)
async def update_bug(data: MainData, authorized: bool = Depends(verify_token)):
    """
    PATCH method for http request on '/bug' for updating an existing UP in the AI.
    Returns
    -------
    A message with a brief description explaining the result for the request and status code.
    """
    if authorized:
        try:
            status, message = await ai.update_bug(**data.dict())
        except ValueError:
            raise HTTPException(status_code=404, detail= Message.NO_USER.value)

        return JSONResponse(content={'detail': message.value}, status_code=status.value)
    return JSONResponse(content={'Unauthorized'}, status_code=401)

@app.delete('/bug', status_code= 200)
async def delete_bug(data: DeleteData, authorized: bool = Depends(verify_token)):
    """
    Method for handling a delete request on /bug for removing an existing UP in the AI.
    Returns
    -------
    A message with a brief description of the result for the request and status code.
    """
    if authorized:
        try:
            status, message = await ai.remove_bug(**data.dict())
        except ValueError:
            raise HTTPException(status_code=404, detail= Message.NO_USER.value)

        return JSONResponse(content={'detail': message.value}, status_code=status.value)

    return JSONResponse(content={'Unauthorized'}, status_code=401)

@app.delete('/batch', status_code= 200)
async def delete_batch(data: DeleteBatchData, authorized: bool = Depends(verify_token)):
    """
    Method for handling delete request on /batch, used for deleting a batch of UPs
    Returns
    -------
    Message with a brief explanation and status code
    """
    if authorized:
        try:
            status, message = await ai.remove_batch(**data.dict())
        except ValueError:
            raise HTTPException(status_code=404, detail= Message.NO_USER.value)

        return JSONResponse(content={'detail': message.value}, status_code=status.value)

    return JSONResponse(content={'Unauthorized'}, status_code=401)

@app.post('/batch', status_code= 200)
async def insert_batch(data: BatchData, authorized: bool = Depends(verify_token)):
    """
    Method for handling a post request on '/batch'.
    Used for inserting multiple examples at once.
    Returns
    -------
    Message with brief explanation and status code
    """

    if authorized:
        try:
            status, message = await ai.add_batch(**data.dict())
        except ValueError:
            raise HTTPException(status_code=404, detail= Message.NO_USER.value)
        except AssertionError:
            raise HTTPException(status_code=400,
                detail= ('Each example must contain same "batch_id" '
                'and either summary or description must be a valid non-empty string'))

        return JSONResponse(content={'detail': message.value}, status_code=status.value)

    return JSONResponse(content={'Unauthorized'}, status_code=401)
