# pylint: disable=R0201
# pylint: disable=E0611
# pylint: disable=R0903
# pylint: disable=W0707
# pylint: disable=W0613
"""
@authors: Gitcelo, natidemis
May-June 2021

API for AI web service
"""


import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from bcj_ai import BCJMessage, BCJAIapi as AI
from Misc.datamodels import (BatchDataModel,
                        GetDataModel,
                        MainDataModel,
                        DeleteDataModel,
                        DeleteBatchDataModel)
from Misc.db import Database, NotFoundError
from Misc.log import logger

load_dotenv()
secret_token = os.getenv('SECRET_TOKEN')
app = FastAPI()

ai_manager: AI #pylint: disable=invalid-name
database: Database #pylint: disable=invalid-name


def verify_token(req: Request):
    """
    Authenticate request via SECRET_TOKEN
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
    """
    Initialize database and all relevant objects
    """
    logger.info('Starting app..')
    reset = os.getenv('RESET','RESET=True not in env')

    global database #pylint: disable=global-statement,invalid-name
    database = await Database.connect_pool()
    setup = await database.setup_database(reset=reset == 'True')

    #Only start up if database has been successfully setup
    if not setup:
        sys.exit()

    global ai_manager #pylint: disable=global-statement,invalid-name
    ai_manager = await AI.initalize(database)



@app.on_event("shutdown")
async def shut_down():
    """
    Close nessary variables
    """
    await database.close_pool()
    logger.info("Server shutting down..")


@app.get('/bug', status_code=200)
async def k_most_similar_bugs(data: GetDataModel, authorized: bool = Depends(verify_token)):
    """
    GET method that fetches the k UPs that are most similar to the UP

    Arguments
    ---------
    data - GetDataModel
        pydantic.BaseModel object that validates the json
        with the request.

    authorized - Depends
        Validates authorized access via 'verify_token'
    Returns
    -------
    ID's and dists of the k most similar bugs if successful request, else an error message &
    Status code
    """


    try:
        bugs = await ai_manager.get_similar_bugs_k(**data.dict())
    except ValueError :
        raise HTTPException(status_code=404, detail=BCJMessage.NO_USER.value)
    except AssertionError:
        raise HTTPException(status_code=400,detail=BCJMessage.UNFULFILLED_REQ.value)
    except NotFoundError:
        raise HTTPException(status_code=404, detail= BCJMessage.EMPTY_TREE.value)
    return JSONResponse(content=bugs[1], status_code=bugs[0].value)




@app.post('/bug', status_code=200)
async def insert_bugs(data: MainDataModel, authorized: bool = Depends(verify_token)):
    """
    Method for handling POST request on '/bug',
    Used for inserting a bug to the AI and its database.

    Arguments
    ---------
    data - MainDataModel
        pydantic.BaseModel object that validates the json
        with the request.

    authorized - Depends
        Validates authorized access via 'verify_token'

    Returns
    -------
    A message with a brief description explaining the result for the request and status code.
    """

    try:
        status, message = await ai_manager.add_bug(**data.dict())
    except ValueError:
        raise HTTPException(status_code=404, detail= BCJMessage.NO_USER.value)
    except AssertionError:
        raise HTTPException(status_code=404, detail= BCJMessage.UNFULFILLED_REQ.value)
    return JSONResponse(content={'detail': message.value}, status_code=status.value)

@app.patch('/bug', status_code= 200)
async def update_bug(data: MainDataModel, authorized: bool = Depends(verify_token)):
    """
    Method for patch http request on '/bug' for updating an existing bug in the AI.

    Arguments
    ---------
    data - MainDataModel
        pydantic.BaseModel object that validates the json
        with the request.

    authorized - Depends
        Validates authorized access via 'verify_token'
    Returns
    -------
    A message with a brief description explaining the result for the request and status code.
    """

    try:
        status, message = await ai_manager.update_bug(**data.dict())
    except ValueError:
        raise HTTPException(status_code=404, detail= BCJMessage.NO_USER.value)
    return JSONResponse(content={'detail': message.value}, status_code=status.value)


@app.delete('/bug', status_code= 200)
async def delete_bug(data: DeleteDataModel, authorized: bool = Depends(verify_token)):
    """
    Method for handling a delete request on '/bug' for deleting an existing bug in the AI.

    Arguments
    ---------
    data - GetDataModel
        pydantic.BaseModel object that validates the json
        with the request.

    authorized - Depends
        Validates authorized access via 'verify_token'

    Returns
    -------
    A message with a brief description of the result for the request and status code.
    """
    try:
        status, message = await ai_manager.remove_bug(**data.dict())
    except ValueError:
        raise HTTPException(status_code=404, detail= BCJMessage.NO_USER.value)
    return JSONResponse(content={'detail': message.value}, status_code=status.value)


@app.delete('/batch', status_code= 200)
async def delete_batch(data: DeleteBatchDataModel, authorized: bool = Depends(verify_token)):
    """
    Method for handling delete request on '/batch', used for deleting a batch of bugs

    Arguments
    ---------
    data - DeleteBatchDataModel
        pydantic.BaseModel object that validates the json
        with the request.

    authorized - Depends
        Validates authorized access via 'verify_token'

    Returns
    -------
    Message with a brief explanation and status code
    """

    try:
        status, message = await ai_manager.remove_batch(**data.dict())
    except ValueError:
        raise HTTPException(status_code=404, detail= BCJMessage.NO_USER.value)
    return JSONResponse(content={'detail': message.value}, status_code=status.value)


@app.post('/batch', status_code= 200)
async def insert_batch(data: BatchDataModel, authorized: bool = Depends(verify_token)):
    """
    Method for handling a post request on '/batch'.
    Used for inserting multiple bugs at once.

    Arguments
    ---------
    data - BatchDataModel
        pydantic.BaseModel object that validates the json
        with the request.

    authorized - Depends
        Validates authorized access via 'verify_token'

    Returns
    -------
    Message with brief explanation and status code
    """

    try:
        status, message = await ai_manager.add_batch(**data.dict())
    except ValueError:
        raise HTTPException(status_code=404, detail= BCJMessage.NO_USER.value)
    except AssertionError:
        raise HTTPException(status_code=400,
            detail= ('Each example must contain same "batch_id" '
            'and either summary or description must be a valid non-empty string'))
    return JSONResponse(content={'detail': message.value}, status_code=status.value)
