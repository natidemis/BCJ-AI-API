#pylint: disable=E0401
#pylint: disable=W0621
#pylint: disable=C0103
#pylint: disable=C0413
#pylint: disable=W0612
"""
@author Gitcelo
July 2021

Test module for testing functions in `bcj_ai.py`
"""

import sys
import os
import random
import datetime
import lorem
import pytest
import pandas as pd

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

from bcj_ai import BCJAIapi, BCJStatus
from helper import Message
from db import Database, NotFoundError
################
### FIXTURES ###
################


@pytest.fixture
def ai():
    """
    Class to be tested
    """
    return BCJAIapi()

@pytest.fixture
def N():
    """
    Arbitrary value high enough to test multiple cases
    """
    return 30

@pytest.fixture
def database():
    """
    Class to access and operate on the database.
    Used in conjunction with 'ai'
    """
    return Database()

@pytest.fixture
def no_desc_and_summ(N):
    """
    Random date without description and summary
    """
    return zip(
        list(range(N)) ,
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
    """
    Data containing a duplicate key
    """
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
def get_random_date(year='2015'):
    """
    Random date generator for year '2015'
    """
    # try to get a date
    try:
        return datetime.datetime.strptime('{} {}'.format(random.randint(1, 366), year), '%j %Y')

    # if the value happens to be in the leap year range, try again
    except ValueError:
        return get_random_date(year)

@pytest.fixture
def valid_batch_data(get_random_date):
    """
    Valid batch data using the CUE-9 dataset
    """
    df = pd.read_excel('CUE-9 Reports 1 - All Teams.xlsx')
    return [
        {
            'summary': '',
            'description': row[2],
            'structured_info': {
                'id': _id,
                'batch_id': 1,
                'date': str(get_random_date)[0:10]
            }
        } for _id, row in df.iterrows()]

@pytest.fixture
def duplicate_id_batch_data(get_random_date):
    """
    Dataset containing duplicate ids
    """
    df = pd.read_excel('CUE-9 Reports 1 - All Teams.xlsx')
    return [
        {
            'summary': '',
            'description': row[2],
            'structured_info': {
                'id': 1,
                'batch_id': 1,
                'date': str(get_random_date)[0:10]
            }
        } for _id, row in df.iterrows()]


@pytest.fixture
def invalid_batch_data_missing_text(get_random_date):
    """
    Dataset missing summary and description
    """
    df = pd.read_excel('CUE-9 Reports 1 - All Teams.xlsx')
    return [
        {
            'summary': '',
            'description': '',
            'structured_info': {
                'id': _id,
                'batch_id': 1,
                'date': str(get_random_date)[0:10]
            }
        } for _id in df.iterrows()]


@pytest.fixture
def invalid_batch_data(get_random_date):
    """
    Dataset containing valid date
    but doesn't conform to the constraint of having the same "batch_id"
    for each example.
    """
    df = pd.read_excel('CUE-9 Reports 1 - All Teams.xlsx')
    return [
        {
            'summary': '',
            'description': row[2],
            'structured_info': {
                'id': _id,
                'batch_id': random.randint(1,100000),
                'date': str(get_random_date)[0:10]
            }
        } for _id, row in df.iterrows()]

@pytest.fixture
def valid_data(N):
    """
    Valid date for 'user_id': 1
    """
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

def test_add_bug_no_desc_and_summ_available(no_desc_and_summ):
    """
    @ai.add_bug()
    Tests for assertionError if both
    'summary' and 'description'
    don't satisfy the 'bool' function.
    """
    ai = BCJAIapi()
    for user_id, structured_info, summ, disc in no_desc_and_summ:
        try:
            ai.add_bug(user_id=user_id,
                        structured_info=structured_info,
                        summary="",#summ = None
                        description=disc) #disc = None
            assert False
        except AssertionError:
            assert True

def test_add_bug_duplicate_key(duplicate_key_data,database):
    """
    @ai.add_bug()
    Duplicate key testing.
    Performs:
        - Adding in an already existing key.
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
    ai.users = {1}
    database.insert_user(1)
    database.insert(1,1,[1,1])
    for user_id, structured_info, summ, disc in duplicate_key_data:
        status, message = ai.add_bug(user_id=user_id,
                        structured_info=structured_info,
                        summary="summary",#summ = None
                        description="description") #disc = None
        assert BCJStatus.BAD_REQUEST == status and \
            Message.DUPLICATE_ID == message
    database.drop_table()
    database.make_table()

def test_add_bug_valid_data(valid_data,database):
    """
    @ai.add_bug()
    Tests for valid input.
    Performs:
        - Tests adding in new users to the database.
        - Tests for valid insert into the database and KDTree
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
    for user_id, structured_info, summ, disc in valid_data:

        status, message = ai.add_bug(user_id=user_id,
                                    structured_info=structured_info,
                                    summary=summ,#summ = None
                                    description=disc) #disc = None
        assert BCJStatus.OK == status and \
            Message.VALID_INPUT == message

    database.drop_table()
    database.make_table()


###############################
### ai.get_similar_bugs_k() ###
###############################

def test_similar_bugs_k_no_desc_and_summ_available(no_desc_and_summ,database):
    """
    @ai.add_bug()
    Tests for assertionError if both
    'summary' and 'description'
    don't satisfy the 'bool' function.
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
    for user_id, structured_info, summ, disc in no_desc_and_summ:
        structured_info['id'] += 100
        try:
            ai.add_bug(user_id=user_id,
                        structured_info=structured_info,
                        summary="summary")
        except AssertionError:
            pass
        try:
            ai.get_similar_bugs_k(user_id=user_id,
                    structured_info=structured_info,
                    summary="",#summ = None
                    description=disc) #disc = None
            assert False
        except AssertionError:
            assert True

    database.drop_table()
    database.make_table()


def test_similar_bugs_k_no_data(database,N):
    """
    @ai.add_bug()
    Tests for fetching the 'k' most similar
    when no data is available for user.
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
    for user_id in range(2,N):
        #add a bunch of data for user_id 1
        ai.add_bug(user_id=1,
                    structured_info={'id': user_id,
                                    'date': '2020-10-10'},
                    summary="summary",
                    description="description")
        #Database is empty for this user_id
        try:
            #add user_id to the users database without inserting embeddings.
            ai.add_bug(user_id=user_id,
                        structured_info={'id': user_id,
                                        'date': '2020-10-10'})
        except AssertionError:
            pass

        status, message = ai.get_similar_bugs_k(user_id=user_id,
                                                structured_info={'date': 'YYYY-MM-DD'},
                                                summary="summary",
                                                description="") #disc = None
        assert BCJStatus.NOT_FOUND == status and \
        message == 'No examples available'


    database.drop_table()
    database.make_table()


def test_similar_bugs_k_valid_input_no_k(valid_data,database):
    """
    @ai.add_bug()
    Tests for fetching 'k' most similar with the default value for k.
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
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


def test_similar_bugs_k_valid_input_w_k(valid_data,database,N):
    """
    @ai.add_bug()
    Tests fetch the 'k' most similar
    with an arbitrary value of k
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
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
### ai.remove_bug() ###########
###############################


def test_remove_bug_valid_delete(database,N):
    """
    @ai.remove_bug()
    Tests for removing an existing example from the database
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
    for i in range(N):
        ai.add_bug(user_id=1,
            structured_info= {'id': i},
            summary="summary",
            description="description")
        status, message = ai.remove_bug(id=i,user_id=1)
        assert BCJStatus.OK == status and \
            Message.VALID_INPUT == message

    database.drop_table()
    database.make_table()


def test_remove_bug_no_valid_id(database,N):
    """
    @ai.remove_bug()
    Tests for removing a non existent example from the database.
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
    ai.add_bug(user_id=1,
            structured_info= {'id': 1},
            summary="summary",
            description="description")

    for _ in range(N):
        status, message = ai.remove_bug(id=random.randint(2,N),user_id=1)
        assert BCJStatus.NOT_FOUND == status and \
            Message.VALID_INPUT == message

    database.drop_table()
    database.make_table()

###############################
### ai.update_bug() ###########
###############################

def test_update_bug_no_summ_and_desc_update_batch_id(database):
    """
    @ai.update_bug()
    Tests for updating batch_id alone.
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
    ai.add_bug(user_id=1,
            structured_info= {'id': 1},
            summary="summary", description= "description")

    status, message = ai.update_bug(user_id=1,structured_info={'id': 1,'batch_id': 1})
    assert BCJStatus.OK == status and \
        Message.VALID_INPUT == message

    database.drop_table()
    database.make_table()

def test_update_bug_no_summ_and_desc_update_batch_id_to_none(database,N):
    """
    @ai.update_bug()
    Tests for updating a batch_id to None(null) in the database
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
    for i in range(N):
        ai.add_bug(user_id=i,
                structured_info= {'id': 1},
                summary="summary", description= "description")
        status, message = ai.update_bug(user_id=i,structured_info={'id': 1, 'batch_id': None})
        assert status == BCJStatus.OK and message == \
            Message.VALID_INPUT
    database.drop_table()
    database.make_table()

def test_update_bug_no_summ_and_desc_update_nothing(database,N):
    """
    @ai.update_bug()
    Testing updates without any updatable value.
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
    for i in range(N):
        ai.add_bug(user_id=i,
                structured_info= {'id': 1,'batch_id': None},
                summary="summary", description= "description")
        status, message = ai.update_bug(user_id=i,structured_info={'id': 1})
        assert status == BCJStatus.NOT_FOUND and message == \
            Message.NO_UPDATES
    database.drop_table()
    database.make_table()


def test_update_bug_on_non_existing_data(database,N):
    """
    @ai.update_bug()
    Tests update on non existent example
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
    for i in range(N):
        ai.add_bug(user_id=i,
                structured_info= {'id': 1,'batch_id': None},
                summary="summary", description= "description")
        status, message = ai.update_bug(user_id=i,
                                        structured_info={'id': 2},
                                        summary="summary",
                                        description= "description")
        assert status == BCJStatus.NOT_FOUND and message == \
            Message.NO_UPDATES
    database.drop_table()
    database.make_table()

def test_update_bug_on_valid_data(database,N):
    """
    @ai.update_bug()

    Tests for valid update on an existing example
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
    for i in range(N):

        ai.add_bug(user_id=i,
                structured_info= {
                    'id': 1,
                    'batch_id': random.choice([None,random.randint(0,10)])},
                summary="summary",
                description= "description")
        status, message = ai.update_bug(user_id=i,
                                        structured_info={'id': 1},
                                        summary="new summary")
        assert status == BCJStatus.OK and message == \
            Message.VALID_INPUT
    database.drop_table()
    database.make_table()


###############################
### ai.add_batch() ############
###############################

def test_add_batch_valid_data(database, valid_batch_data):
    """
    @ai.add_batch()
    Tests inserting valid chunk of batches.
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()

    user_id = 1
    data = {
        'user_id': user_id,
        'data': valid_batch_data
    }
    status, message = ai.add_batch(**data)
    assert status == BCJStatus.OK and \
        message == Message.VALID_INPUT


def test_add_batch_valid_data_batch_id_error(database, invalid_batch_data):
    """
    @ai.add_batch()
    Tests inserting invalid data.
    Tests for assertion error, all batch_id must be the same
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()

    user_id = 1
    data = {
        'user_id': user_id,
        'data': invalid_batch_data
    }
    try:
        ai.add_batch(**data)
        assert False
    except AssertionError:
        assert True


def test_add_batch_valid_data_missing_text(database, invalid_batch_data_missing_text):
    """
    @ai.add_batch()
    Tests inserting invalid data.
    Tests for assertion error, summary or description
    must be a non-empty string.
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()

    user_id = 1
    data = {
        'user_id': user_id,
        'data': invalid_batch_data_missing_text
    }
    try:
        ai.add_batch(**data)
        assert False
    except AssertionError:
        assert True


def test_add_batch_duplicate_key(database, duplicate_id_batch_data):
    """
    @ai.add_batch()
    Tests inserting invalid data.
    Tests for assertion error, summary or description
    must be a non-empty string.
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()

    user_id = 1
    data = {
        'user_id': user_id,
        'data': duplicate_id_batch_data
    }

    status, message = ai.add_batch(**data)
    assert status == BCJStatus.BAD_REQUEST and \
        message == Message.DUPLICATE_ID_BATCH

##################################
### ai.delete_batch() ############
##################################

def test_remove_batch_no_updates(database,valid_batch_data):
    """
    @ai.remove_batch()
    Tests:
        Removing a non-existing batch
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
    user = 1

    #valid_data has batch_id=1
    data = {
        'user_id': 1,
        'data': valid_batch_data
    }
    ai.add_batch(**data)

    status, message = ai.remove_batch(user_id=user,batch_id=2)
    assert status == BCJStatus.ERROR and \
        message == Message.NO_DELETION


def test_remove_batch_valid_remove(database,valid_batch_data):
    """
    @ai.remove_batch()
    Tests:
        removing an existing batch
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
    user = 1

    #valid_data has batch_id=1
    data = {
        'user_id': 1,
        'data': valid_batch_data
    }
    ai.add_batch(**data)

    status, message = ai.remove_batch(user_id=user,batch_id=1)
    assert status == BCJStatus.OK and \
        message == Message.VALID_INPUT

#############################################
### KDTree and Database cohesion ############
#############################################

def test_db_and_kdtree_equivalency_on_delete(ai,valid_batch_data,database,N):
    """
    Tests for KDTree and database cohesion

    Tests
        - Adding a batch of data
        -removing bugs
        -removing a batch
        - empty database
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()
    user = 1
    data = {
        'user_id': user,
        'data': valid_batch_data
    }
    #add a batch and assert that kdtree and database contains same data.
    ai.add_batch(**data)
    db_data = database.fetch_all(user)
    db_ids = [data['id'] for data in db_data]
    db_embeddings = []
    db_embeddings = [data['embeddings'] for data in db_data]
    kdtree_ids = ai.kdtree.local_indices.tolist()
    kdtree_embeddings = ai.kdtree.data.tolist()
    assert kdtree_embeddings == db_embeddings and db_ids == kdtree_ids

    #delete values and assert that kdtree and database contain the same data
    for i in range(N):
        ai.remove_bug(user_id=user, id=i)
        db_data = database.fetch_all(user)
        kdtree_ids = ai.kdtree.local_indices.tolist()
        kdtree_embeddings = ai.kdtree.data.tolist()
        db_ids = [data['id'] for data in db_data]
        db_embeddings = [data['embeddings'] for data in db_data]
        assert kdtree_embeddings == db_embeddings and db_ids == kdtree_ids

    #remove everything this user has put in, the batch with batch_id = 1.
    ai.remove_batch(user_id= user,batch_id=1)
    try:
        database.fetch_all(user)
        assert False
    except NotFoundError:
        assert ai.kdtree is None

def test_kdtree_and_db_equivalency_multiple_users(ai,database):
    """
    KDtree and db cohesion
    Test fetching the correct data for a user.
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()

    ##
    first_user = 1
    for _id in range(2):
        ai.add_bug(user_id= first_user,
                    structured_info= {
                        'id': _id,
                    },
                    summary='summary',
                    description='description'
        )
    second_user = 2
    ai.add_bug(user_id= second_user,
                    structured_info= {
                        'id': 1,
                    },
                    summary='summary',
                    description='description'
        )

    db_data = database.fetch_all(second_user)
    try:
        kdtree_ids = ai.kdtree.local_indices.tolist()
    except AttributeError:
        kdtree_ids = ai.kdtree.local_indices
    kdtree_embeddings = ai.kdtree.data.tolist()
    db_ids = [data['id'] for data in db_data]
    db_embeddings = []
    for data in db_data:
        db_embeddings.extend(data['embeddings'])
    assert kdtree_embeddings == db_embeddings and db_ids == kdtree_ids
    assert len(kdtree_ids) == 1 and len(kdtree_embeddings) == 1


def test_kdtree_and_db_equivalency_update_bug(ai,database):
    """
    KDtree and db cohesion
    Test fetching the correct data for a user.
    """
    database.drop_table()
    database.make_table()
    ai = BCJAIapi()


    user = 1

    ai.add_bug(user_id= user,
                structured_info= {
                    'id': 1,
                },
                summary='summary',
                description='description'
    )

    ai.update_bug(user_id= user,
                    structured_info= {
                        'id': 1,
                    },
                    summary='new summary',
                    description='new description'
        )

    db_data = database.fetch_all(user)
    db_ids = [data['id'] for data in db_data]
    db_embeddings = []
    for data in db_data:
        db_embeddings.extend(data['embeddings'])
    kdtree_ids = ai.kdtree.local_indices.tolist()
    kdtree_embeddings = ai.kdtree.data.tolist()
    assert kdtree_embeddings == db_embeddings and db_ids == kdtree_ids
