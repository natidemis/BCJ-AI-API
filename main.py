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
from dotenv import load_dotenv
import types
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from bcj_ai import BCJAIapi as AI
from helper import Message
from datamodels import (BatchDataModel,
                        GetDataModel,
                        MainDataModel,
                        DeleteDataModel,
                        DeleteBatchDataModel)
from db import Database
from log import logger

load_dotenv()
secret_token = os.getenv('SECRET_TOKEN')
app = FastAPI()

ai = None

# TODO: Set Limit on summary and description #pylint: disable=W0511
# TODO: take in command-line-argument to reset the database.
# TODO: make fetch_vectors and gen_token a setup.py file.

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

@app.on_event("startup")
async def startup_event():
    """Setup database"""
    logger.info('Starting application')
    reset = os.getenv('RESET','RESET=True not in env')
    await Database().setup_database(reset=reset == 'True')
    global ai 
    ai = await AI()



@app.on_event("shutdown")
def shut_down():
    logger.info("Server shutting down..")


@app.get('/bug', status_code=200)
async def k_most_similar_bugs(data: GetDataModel, authorized: bool = Depends(verify_token)):
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
async def insert_bugs(data: MainDataModel, authorized: bool = Depends(verify_token)):
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
async def update_bug(data: MainDataModel, authorized: bool = Depends(verify_token)):
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
async def delete_bug(data: DeleteDataModel, authorized: bool = Depends(verify_token)):
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
async def delete_batch(data: DeleteBatchDataModel, authorized: bool = Depends(verify_token)):
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
async def insert_batch(data: BatchDataModel, authorized: bool = Depends(verify_token)):
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
