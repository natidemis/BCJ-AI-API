#pylint: disable=E0401
#pylint: disable=W0621
#pylint: disable=C0103
#pylint: disable=C0413
#pylint: disable=E1121
#pylint: disable=W0702
"""
@author natidemis
April 2021

Test module for testing database methods
"""

import sys
import os
import random
import pytest
import numpy as np

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

from db import Database, NotFoundError, DuplicateKeyError


################
### FIXTURES ###
################

@pytest.fixture
def rng():
    """ Return default random generator """
    return np.random.default_rng()

@pytest.fixture
def database():
    """Our db.Database to be tested"""
    return Database()


@pytest.fixture
def valid_data(rng):
    """
    Data in insertable format
    """
    N = 10

    return zip(list(range(N)),
                list(range(N)),
                [rng.random(128) for _ in range(N)],
                [random.choice([random.randint(0,10),None]) for _ in range(N)])

@pytest.fixture
def duplicate_data(rng):
    """
    Data containing multiple duplicate keys
    """
    N = 10
    keys = [1 for i in range(1,N)]
    return zip(keys,
                keys,
                [rng.random(128) for _ in range(N)],
                [random.choice([range(1,N),None]) for _ in range(N)])



###################
### db.insert() ###
###################



def test_valid_insert(database, valid_data):
    """
    @db.insert()
    ------------
    Tests for valid insert
    Performs:
        - inserting random valid input
    """
    database.drop_table()
    database.make_table()
    for _id,user_id,embeddings,batch_id in valid_data:
        database.insert_user(user_id=user_id)
        database.insert(_id=_id,
                        user_id=user_id,
                        embeddings=embeddings,
                        batch_id=batch_id)



def test_invalid_insert_no_user(database, valid_data):
    """
    @db.insert()
    ------------
    Tests for valid insert
    Performs:
        - inserts user without user existing in user table.

    """
    database.drop_table()
    database.make_table()
    for _id,user_id,embeddings,batch_id in valid_data:
        try:
            database.insert(_id=_id,
                        user_id=user_id,
                        embeddings=embeddings,
                        batch_id=batch_id)
            assert False
        except(NotFoundError, DuplicateKeyError):
            assert True



def test_invalid_insert_duplicate_key(database, duplicate_data):
    """
    @db.insert()
    ------------
    Tests for valid insert
    Performs:
        - inserts user as string, not an int.

    """
    database.drop_table()
    database.make_table()
    database.insert_user(1)

    database.insert(1,1,[1,2])
    for _id,user_id,embeddings,batch_id in duplicate_data:
        try:
            database.insert(_id=_id,
                        user_id=user_id,
                        embeddings=embeddings,
                        batch_id=batch_id)
            assert False
        except:
            assert True


########################
### db.insert_user() ###
########################

def test_invalid_insert_user_duplicate_key(database):
    """
    @db.insert_user()
    ------------
    Tests for DuplicateKeyError
    Performs:
        - inserts an already existing key

    """
    database.drop_table()
    database.make_table()
    database.insert_user(1)
    for user_id in zip([1 for i in range(0,10)]):
        try:
            database.insert_user(user_id=user_id)
            assert False
        except:
            assert True

def test_invalid_insert_user_typeError(database):
    """
    @db.insert_user()
    ------------
    Tests for TypeError
    Performs:
        - inserts a non integer value

    """
    database.drop_table()
    database.make_table()

    for user_id in zip([
        random.choice(["string",[1,2],set(),dict()])
            for i in range(0,10)]):
        try:
            database.insert_user(user_id=user_id)
            assert False
        except:
            assert True

#########################
### db.insert_batch() ###
#########################

def test_valid_insert_batch(database,valid_data):
    """
    @db.insert_batch()
    ------------
    Tests for valid insert on batch
    Performs:
        - inserting random valid input
    """
    database.drop_table()
    database.make_table()
    data = []
    for _id,user_id,embeddings,batch_id in valid_data: #pylint: disable=unused-variable
        database.insert_user(user_id)
        data.append((_id,user_id,embeddings,1))
    database.insert_batch(data)



######################
### db.fetch_all() ###
######################

def test_fetch_all_empty(database):
    """
    @db.fetch_all()
    --------------

    Tests NoFoundError
    performs:
        - fetches all from a user with an empty database
    """
    database.drop_table()
    database.make_table()
    try:
        database.fetch_all(1)
        assert False
    except:
        assert True

def test_fetch_all_w_data(database, valid_data):
    """
    @db.insert()
    ------------
    Tests for valid insert
    Performs:
        - inserting random valid input
    """
    database.drop_table()
    database.make_table()
    for _id,user_id,embeddings,batch_id in valid_data:
        database.insert_user(user_id=user_id)
        database.insert(_id=_id,
                        user_id=user_id,
                        embeddings=embeddings,
                        batch_id=batch_id)
        assert isinstance(database.fetch_all(user_id=user_id),list)


###################
### db.update() ###
###################

def test_valid_all_updates(database, valid_data,rng):
    """
    @db.update()
    ------------
    Tests all combination of possible updates
    """
    test_valid_insert(database,valid_data)
    for embeddings in [rng.random(128),None]:
        for batch_id in [random.randint(0,100),None]:
            database.update(0,0,embeddings,batch_id)



def test_updates_no_user(database,valid_data):
    """
    @db.update()
    ------------
    Tests for NoUpdatesError
    """
    #reset the database and add values with ids [0,10]
    test_valid_insert(database,valid_data)

    for _id in range(100,150):
        try:
            database.update(_id=_id,user_id=_id)
            assert False
        except:
            assert True

####################
### db.delete() ###
###################

def test_delete_valid(database,valid_data):
    """
    @db.delete()

    Tests for deleting existing data
    """
    test_valid_insert(database,valid_data)
    N = 10
    for idx in range(N):
        database.delete(_id=idx,user_id=idx)

def test_delete_invalid(database,valid_data):
    """
    @db.delete()

    Tests for deleting non existing data,
    NoUpdatesError test
    """
    test_valid_insert(database,valid_data)
    N = 10
    for idx in range(N+1,N*2):
        try:
            database.delete(_id=idx,user_id=idx)
            assert False
        except:
            assert True

####################
### db.delete() ###
###################

def test_delete_batch_valid(database,valid_data):
    """
    @db.delete_batch()

    Tests for deleting existing data
    """
    test_valid_insert_batch(database,valid_data)
    N = 10
    batch_id = 1
    for idx in range(N):
        database.delete_batch(batch_id=batch_id,user_id=idx)


def test_delete_batch_invalid(database,valid_data):
    """
    @db.delete_batch()

    Tests for deleting existing data
    """
    test_valid_insert_batch(database,valid_data)
    N = 10
    batch_id = 1
    for idx in range(N+1,N*2):
        try:
            database.delete_batch(batch_id=batch_id,user_id=idx)
            assert False
        except:
            assert True

########################
### db.fetch_users() ###
########################

def test_fetch_users_empty(database):
    """
    @db.fetch_users()
    Fetch an empty database
    """
    database.drop_table()
    database.make_table()
    try:
        database.fetch_users()
        assert False
    except:
        assert True

def test_fetch_users_not_empty(database):
    """
    @db.fetch_users()
    Fetch a database with existing data
    """
    database.drop_table()
    database.make_table()
    for i in range(10):
        database.insert_user(i)

    assert isinstance(database.fetch_users(),list)
