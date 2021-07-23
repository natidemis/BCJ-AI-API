"""
@author natidemis
April 2021

Test module for testing database methods
"""

import sys,os
import pytest
import numpy as np
import random
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

from db import Database


################
### FIXTURES ###
################

@pytest.fixture
def rng():
    """ Return default random generatotr """
    return np.random.default_rng()

@pytest.fixture
def database():
    return Database()

def test_valid_insert(database):
    """ Tests for valid insert"""
    database.drop_table()
    database.make_table()
    for _id,user in zip([i for i in range(0,10)],[j for j in range(0,10)]):
        database.insert_user(user_id=user)
        database.insert(_id=_id,
                        user_id=user,
                        embeddings=np.random.rand(100,300),
                        batch_id=random.choice([_id,None]))

def test_invalid_insert_no_user(database,rng):
    """ 
    Tests for valid insert
    Performs: 
        - inserts user without user existing in user table.
        
    """
    database.drop_table()
    database.make_table()
    for _id,user in zip([i for i in range(0,10)],[j for j in range(0,10)]):
        try:
            database.insert(_id=_id,
                        user_id=user,
                        embeddings=rng.random(128),
                        batch_id=random.choice([_id,None]))
            assert False
        except:
            assert True

def test_invalid_insert_str(database, rng):
    """ 
    Tests for valid insert
    Performs: 
        - inserts user as string, not an int.
        
    """
    database.drop_table()
    database.make_table()
    database.insert_user(1)
    for _id,user in zip([i for i in range(0,10)],["1" for j in range(0,10)]):
        try:
            database.insert(_id=_id,
                        user_id=user,
                        embeddings=rng.random(128),
                        batch_id=random.choice([_id,None]))
            assert False
        except:
            assert True
    
