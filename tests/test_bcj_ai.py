"""
@author Gitcelo
July 2021

Test module for testing functions in `bcj_ai.py`
"""

import sys,os
import pytest
import numpy as np
import random
import lorem
import datetime
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

from bcj_ai import BCJAIapi, BCJStatus
from helper import Message 
from db import Database, DuplicateKeyError, NoUpdatesError
################
### FIXTURES ###
################


@pytest.fixture
def ai():
    return BCJAIapi()

@pytest.fixture
def N():
    return 30

@pytest.fixture
def database():
    return Database()

@pytest.fixture
def no_disc_and_summ(N):
    return zip(
        [z for z in range(N)],
        [
            {
            "id": random.randint(1,100),
            "batch_id": random.choice([random.randint(1,10),None])
        } for _ in range(N)],
        [None for _ in range(N)],
        [None for _ in range(N)]
    )

@pytest.fixture
def duplicate_key_data(N):

    return zip(
        [1 for z in range(N)],
        [
            {
            "id": 1,
            "batch_id": random.choice([random.randint(1,10),None])
        } for _ in range(N)],
        [lorem.sentence() for _ in range(N)],
        [lorem.paragraph() for _ in range(N)]
    )

@pytest.fixture
def valid_data(N):
    return zip(
        [1 for z in range(N)],
        [
            {
            "id": z,
            "batch_id": random.choice([random.randint(1,10),None])
        } for z in range(N)],
        ["summary" for _ in range(N)],
        ["description" for _ in range(N)]
    )
####################
### ai.add_bug() ###
####################

def test_add_bug_no_disc_and_summ_available(ai, no_disc_and_summ):
    """
    @ai.add_bug()
    Tests for assertionError if both
    'summary' and 'description'
    don't satisfy the 'bool' function.
    """
    for user_id, structured_info, summ, disc in no_disc_and_summ:
        try:
            ai.add_bug(user_id=user_id,
                        structured_info=structured_info,
                        summary="",#summ = None
                        description=disc) #disc = None
            assert False
        except AssertionError:
            assert True

def test_add_bug_duplicate_key(ai, duplicate_key_data,database):
    """
    @ai.add_bug()
    Duplicate key testing.
    Performs:
        - Adding in an already existing key.
    """
    database.drop_table()
    database.make_table()
    database.insert_user(1)
    database.insert(1,1,[1,1])
    for user_id, structured_info, summ, disc in duplicate_key_data:
        
        assert BCJStatus.BAD_REQUEST, Message.DUPLICATE_ID \
            == ai.add_bug(user_id=user_id,
                        structured_info=structured_info,
                        summary="",#summ = None
                        description=disc) #disc = None
    database.drop_table()
    database.make_table()

def test_add_bug_valid_data(ai, valid_data,database):
    """
    @ai.add_bug()
    Tests for valid input.
    Performs:
        - Tests adding in new users to the database.
        - Tests for valid insert into the database and KDTree
    """
    database.drop_table()
    database.make_table()
    for user_id, structured_info, summ, disc in valid_data:
        
        assert BCJStatus.OK, Message.VALID_INPUT \
            == ai.add_bug(user_id=user_id,
                        structured_info=structured_info,
                        summary=summ,#summ = None
                        description=disc) #disc = None
    database.drop_table()
    database.make_table()


###############################
### ai.get_similar_bugs_k() ###
###############################

def test_similar_bugs_k_no_disc_and_summ_available(ai, no_disc_and_summ,database):
    """
    @ai.add_bug()
    Tests for assertionError if both
    'summary' and 'description'
    don't satisfy the 'bool' function.
    """
    database.drop_table()
    database.make_table()
    for user_id, structured_info, summ, disc in no_disc_and_summ:
        structured_info['id'] += 100
        try:
            ai.add_bug(user_id=user_id,
                        structured_info=structured_info,
                        summary="summary")
        except: 
            pass
        try:
            ai.get_similar_bugs_k(user_id=user_id,
                    structured_info=structured_info,
                    summary="",#summ = None
                    description=disc) #disc = None
            assert False
        except:
            assert True
            
    database.drop_table()
    database.make_table()


def test_similar_bugs_k_no_data(ai, valid_data,database):
    """
    @ai.add_bug()
    Tests for assertionError if both
    'summary' and 'description'
    don't satisfy the 'bool' function.
    """
    database.drop_table()
    database.make_table()
    
    for user_id, structured_info, summ, disc in valid_data:
        try:
            #adds user_id to the database but doesn't insert any values.
            ai.add_bug(user_id=user_id,
                        structured_info=structured_info,
                        summary=summ)
        except: 
            pass
        #Database is empty for this user_id
        assert BCJStatus.NOT_FOUND, 'No examples available' == \
        ai.get_similar_bugs_k(user_id=user_id,
                            structured_info=structured_info,
                            summary=summary,#summ = None
                            description=description) #disc = None
            
            
    database.drop_table()
    database.make_table()


def test_similar_bugs_k_valid_input_no_k(ai, valid_data,database):
    """
    @ai.add_bug()
    Tests for assertionError if both
    'summary' and 'description'
    don't satisfy the 'bool' function.
    """
    database.drop_table()
    database.make_table()
    k = 5 #default value for k in get_similar_bugs_k
    num = 0 #number of bugs in the database
    for user_id, structured_info, summ, desc in valid_data:
    
        ai.add_bug(user_id=user_id,
                    structured_info=structured_info,
                    summary="summary",
                    description= "description")
    for user_id, structured_info, summ, desc in valid_data:
        status, res = ai.get_similar_bugs_k(user_id=user_id,
                    structured_info=structured_info,
                    summary="summary",#summ = None
                    description="description") #disc = None
        num += 1
        assert BCJStatus.OK == status and isinstance(res, dict) \
            and len(res['id']) == len(res['dist']) == min(k,num)
    database.drop_table()
    database.make_table()


def test_similar_bugs_k_valid_input_w_k(ai, valid_data,database,N):
    """
    @ai.add_bug()
    Tests for assertionError if both
    'summary' and 'description'
    don't satisfy the 'bool' function.
    """
    database.drop_table()
    database.make_table()
    k = random.randint(1,N) #default value for k in get_similar_bugs_k
    num = 0 #number of bugs in the database
    for user_id, structured_info, summ, desc in valid_data:
    
        ai.add_bug(user_id=user_id,
                    structured_info=structured_info,
                    summary="summary",
                    description= "description")
    for user_id, structured_info, summ, desc in valid_data:
        status, res = ai.get_similar_bugs_k(user_id=user_id,
                    structured_info=structured_info,
                    summary="summary",#summ = None
                    description="description",
                    k=k) #disc = None
        num += 1
        assert BCJStatus.OK == status and isinstance(res, dict) \
            and len(res['id']) == len(res['dist']) == min(k,num)
    database.drop_table()
    database.make_table()

###############################
### ai.delete_bug() ###########
###############################

def test_remove_bug_no_valid_id(ai,database,N):
    database.drop_table()
    database.make_table()
    ai.add_bug(user_id=1,
            structured_info= {'id': 1},
            summary="summary",
            description="description")

    for _ in range(N):
  
        assert BCJStatus.NOT_FOUND, Message.VALID_INPUT == \
            ai.remove_bug(_id=random.randint(2,N),user_id=1) #remove invalid id pairs.

    database.drop_table()
    database.make_table()

def test_remove_bug_valid_delete(ai,database,N):
    database.drop_table()
    database.make_table()

    for i in range(N):
        ai.add_bug(user_id=1,
            structured_info= {'id': 1},
            summary="summary",
            description="description")

        assert BCJStatus.OK, Message.VALID_INPUT == \
            ai.remove_bug(_id=i,user_id=1) #remove invalid id pairs.

    database.drop_table()
    database.make_table()