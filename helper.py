# pylint: disable=R0201
# pylint: disable=C0301
"""
@author natidemis
June 2021

Helper classes for the app
"""
from enum import Enum

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
    WHERE id = $2 AND user_id = $3 RETURNING *;
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
    UNPROCESSABLE_INPUT = 'Something is wrong with the inserted data.'
    VALID_INPUT = 'Valid input, check status for result'
    FAILURE = '''Data not in proper format, read the requirement on github: https://github.com/natidemis/BCJ-AI-API'''
    UNFULFILLED_REQ = 'Either summary or description must have length > 0'
    UNAUTHORIZED = 'Unauthorized, wrong token'
    REMOVED = 'Successfully removed'
    DUPLICATE_ID = "This Id already exists for the given user"
    DUPLICATE_ID_BATCH = "One of the given bug Id's already exists for this user"
    NO_EXAMPLE = 'There is no example with the the given ID for this user.'
    INVALID_ID_OR_DATE = ("Either the id already exists or "
                "the given date is not valid")
    NO_USER = "User not available."
    NO_UPDATES = "There were no updates to make."
    NO_DELETION = "There was nothing to delete for the given (user_id, id) pair."
