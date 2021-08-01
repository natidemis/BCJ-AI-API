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
@pytest.mark.asyncio
async def ai():
    bcjai = await BCJAIapi()
    return bcjai

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

@pytest.mark.asyncio
async def test_add_bug_no_desc_and_summ_available(ai,database, no_desc_and_summ):
    """
    @ai.add_bug()
    Tests for assertionError if both
    'summary' and 'description'
    don't satisfy the 'bool' function.
    """
    await database.setup_database(reset=True)
    ai.users = set()

    for user_id, structured_info, summ, disc in no_desc_and_summ:
        try:
            satus, message = await ai.add_bug(user_id=user_id,
                        structured_info=structured_info,
                        summary="",#summ = None
                        description=disc) #disc = None
            assert False
        except AssertionError:
            assert True
    await database.setup_database(reset=True)

@pytest.mark.asyncio
async def test_add_bug_duplicate_key(ai,duplicate_key_data,database):
    """
    @ai.add_bug()
    Duplicate key testing.
    Performs:
        - Adding in an already existing key.
    """
    await database.setup_database(reset=True)
    ai.users = set([1])
    await database.insert_user(1)
    await database.insert(1,1,[1,1])
    for user_id, structured_info, summ, disc in duplicate_key_data:
        status, message = await ai.add_bug(user_id=user_id,
                        structured_info=structured_info,
                        summary="summary",#summ = None
                        description="description") #disc = None
        assert BCJStatus.BAD_REQUEST == status and \
            Message.DUPLICATE_ID == message
    await database.setup_database(reset=True)

@pytest.mark.asyncio
async def test_add_bug_valid_data(ai,valid_data,database):
    """
    @ai.add_bug()
    Tests for valid input.
    Performs:
        - Tests adding in new users to the database.
        - Tests for valid insert into the database and KDTree
    """
    await database.setup_database(reset=True)
    ai.users = set()
    for user_id, structured_info, summ, disc in valid_data:

        status, message = await ai.add_bug(user_id=user_id,
                                    structured_info=structured_info,
                                    summary=summ,#summ = None
                                    description=disc) #disc = None
        assert BCJStatus.OK == status and \
            Message.VALID_INPUT == message

    await database.setup_database(reset=True)


###############################
### ai.get_similar_bugs_k() ###
###############################

@pytest.mark.asyncio
async def test_similar_bugs_k_no_desc_and_summ_available(ai,no_desc_and_summ,database):
    """
    @ai.add_bug()
    Tests for assertionError if both
    'summary' and 'description'
    don't satisfy the 'bool' function.
    """
    await database.setup_database(reset=True)
    ai.users = set()
    for user_id, structured_info, summ, disc in no_desc_and_summ:
        structured_info['id'] += 100
        try:
            await ai.add_bug(user_id=user_id,
                        structured_info=structured_info,
                        summary="summary")
        except AssertionError:
            pass
        try:
            await ai.get_similar_bugs_k(user_id=user_id,
                    structured_info=structured_info,
                    summary="",#summ = None
                    description=disc) #disc = None
            assert False
        except AssertionError:
            assert True

    await database.setup_database(reset=True)

@pytest.mark.asyncio
async def test_similar_bugs_k_no_data(ai,database,N):
    """
    @ai.add_bug()
    Tests for fetching the 'k' most similar
    when no data is available for user.
    """
    await database.setup_database(reset=True)
    ai.users = set()
    for user_id in range(2,N):
        #add a bunch of data for user_id 1
        await ai.add_bug(user_id=1,
                    structured_info={'id': user_id,
                                    'date': '2020-10-10'},
                    summary="summary",
                    description="description")
        #Database is empty for this user_id
        try:
            #add user_id to the users database without inserting embeddings.
            await ai.add_bug(user_id=user_id,
                        structured_info={'id': user_id,
                                        'date': '2020-10-10'})
        except AssertionError:
            pass

        status, message = await ai.get_similar_bugs_k(user_id=user_id,
                                                structured_info={'date': 'YYYY-MM-DD'},
                                                summary="summary",
                                                description="") #disc = None
        assert BCJStatus.NOT_FOUND == status and \
        message == 'No examples available'


    await database.setup_database(reset=True)

@pytest.mark.asyncio
async def test_similar_bugs_k_valid_input_no_k(ai,valid_data,database):
    """
    @ai.add_bug()
    Tests for fetching 'k' most similar with the default value for k.
    """
    database.drop_table()
    database.make_table()
    ai.users = set()
    k = 5 #default value for k in get_similar_bugs_k
    num = 0 #number of bugs in the database
    for user_id, structured_info, summ, desc in valid_data:

        await ai.add_bug(user_id=user_id,
                    structured_info=structured_info,
                    summary="summary",
                    description= "description")
    for user_id, structured_info, summ, desc in valid_data:
        status, res = await ai.get_similar_bugs_k(user_id=user_id,
                    structured_info=structured_info,
                    summary="summary",#summ = None
                    description="description") #disc = None
        num += 1
        assert BCJStatus.OK == status and isinstance(res, dict) \
            and len(res['id']) == len(res['dist']) == min(k,num)
    await database.setup_database(reset=True)

@pytest.mark.asyncio
async def test_similar_bugs_k_valid_input_w_k(ai,valid_data,database,N):
    """
    @ai.add_bug()
    Tests fetch the 'k' most similar
    with an arbitrary value of k
    """
    await database.setup_database(reset=True)
    ai.users = set()
    k = random.randint(1,N) #default value for k in get_similar_bugs_k
    num = 0 #number of bugs in the database
    for user_id, structured_info, summ, desc in valid_data:

        await ai.add_bug(user_id=user_id,
                    structured_info=structured_info,
                    summary="summary",
                    description= "description")
    for user_id, structured_info, summ, desc in valid_data:
        status, res = await ai.get_similar_bugs_k(user_id=user_id,
                    structured_info=structured_info,
                    summary="summary",#summ = None
                    description="description",
                    k=k) #disc = None
        num += 1
        assert BCJStatus.OK == status and isinstance(res, dict) \
            and len(res['id']) == len(res['dist']) == min(k,num)
    await database.setup_database(reset=True)

###############################
### ai.remove_bug() ###########
###############################

@pytest.mark.asyncio
async def test_remove_bug_valid_delete(ai,database,N):
    """
    @ai.remove_bug()
    Tests for removing an existing example from the database
    """
    await database.setup_database(reset=True)
    ai.users = set()
    for i in range(N):
        await ai.add_bug(user_id=1,
            structured_info= {'id': i},
            summary="summary",
            description="description")
        status, message = await ai.remove_bug(id=i,user_id=1)
        assert BCJStatus.OK == status and \
            Message.VALID_INPUT == message

    await database.setup_database(reset=True)

@pytest.mark.asyncio
async def test_remove_bug_no_valid_id(ai,database,N):
    """
    @ai.remove_bug()
    Tests for removing a non existent example from the database.
    """
    await database.setup_database(reset=True)
    ai.users = set()
    await ai.add_bug(user_id=1,
            structured_info= {'id': 1},
            summary="summary",
            description="description")

    for _ in range(N):
        status, message = await ai.remove_bug(id=random.randint(2,N),user_id=1)
        assert BCJStatus.NOT_FOUND == status and \
            Message.VALID_INPUT == message

    await database.setup_database(reset=True)

###############################
### ai.update_bug() ###########
###############################

@pytest.mark.asyncio
async def test_update_bug_no_summ_and_desc_update_batch_id(ai,database):
    """
    @ai.update_bug()
    Tests for updating batch_id alone.
    """
    await database.setup_database(reset=True)
    ai.users = set()
    await ai.add_bug(user_id=1,
            structured_info= {'id': 1},
            summary="summary", description= "description")

    status, message = await ai.update_bug(user_id=1,structured_info={'id': 1,'batch_id': 1})
    assert BCJStatus.OK == status and \
        Message.VALID_INPUT == message

    await database.setup_database(reset=True)

@pytest.mark.asyncio
async def test_update_bug_no_summ_and_desc_update_batch_id_to_none(ai,database,N):
    """
    @ai.update_bug()
    Tests for updating a batch_id to None(null) in the database
    """
    await database.setup_database(reset=True)
    ai.users = set()
    for i in range(N):
        await ai.add_bug(user_id=i,
                structured_info= {'id': 1},
                summary="summary", description= "description")
        status, message = await ai.update_bug(user_id=i,structured_info={'id': 1, 'batch_id': None})
        assert status == BCJStatus.OK and message == \
            Message.VALID_INPUT
    await database.setup_database(reset=True)

@pytest.mark.asyncio
async def test_update_bug_no_summ_and_desc_update_nothing(ai,database,N):
    """
    @ai.update_bug()
    Testing updates without any updatable value.
    """
    await database.setup_database(reset=True)
    ai.users = set()
    for i in range(N):
        await ai.add_bug(user_id=i,
                structured_info= {'id': 1,'batch_id': None},
                summary="summary", description= "description")
        status, message = await ai.update_bug(user_id=i,structured_info={'id': 1})
        assert status == BCJStatus.NOT_FOUND and message == \
            Message.NO_UPDATES
    await database.setup_database(reset=True)


@pytest.mark.asyncio
async def test_update_bug_on_non_existing_data(ai,database,N):
    """
    @ai.update_bug()
    Tests update on non existent example
    """
    await database.setup_database(reset=True)
    ai.users = set()
    for i in range(N):
        await ai.add_bug(user_id=i,
                structured_info= {'id': 1,'batch_id': None},
                summary="summary", description= "description")
        status, message = await ai.update_bug(user_id=i,
                                        structured_info={'id': 2},
                                        summary="summary",
                                        description= "description")
        assert status == BCJStatus.NOT_FOUND and message == \
            Message.NO_UPDATES
    await database.setup_database(reset=True)

@pytest.mark.asyncio
async def test_update_bug_on_valid_data(ai,database,N):
    """
    @ai.update_bug()

    Tests for valid update on an existing example
    """
    await database.setup_database(reset=True)
    ai.users = set()
    for i in range(N):

        await ai.add_bug(user_id=i,
                structured_info= {
                    'id': 1,
                    'batch_id': random.choice([None,random.randint(0,10)])},
                summary="summary",
                description= "description")
        status, message = await ai.update_bug(user_id=i,
                                        structured_info={'id': 1},
                                        summary="new summary")
        assert status == BCJStatus.OK and message == \
            Message.VALID_INPUT
    await database.setup_database(reset=True)


###############################
### ai.add_batch() ############
###############################

@pytest.mark.asyncio
async def test_add_batch_valid_data(ai,database, valid_batch_data):
    """
    @ai.add_batch()
    Tests inserting valid chunk of batches.
    """
    await database.setup_database(reset=True)
    ai.users = set()

    user_id = 1
    data = {
        'user_id': user_id,
        'data': valid_batch_data
    }
    status, message = await ai.add_batch(**data)
    assert status == BCJStatus.OK and \
        message == Message.VALID_INPUT

@pytest.mark.asyncio
async def test_add_batch_valid_data_batch_id_error(ai, database, invalid_batch_data):
    """
    @ai.add_batch()
    Tests inserting invalid data.
    Tests for assertion error, all batch_id must be the same
    """
    await database.setup_database(reset=True)
    ai.users = set()

    user_id = 1
    data = {
        'user_id': user_id,
        'data': invalid_batch_data
    }
    try:
        await ai.add_batch(**data)
        assert False
    except AssertionError:
        assert True


@pytest.mark.asyncio
async def test_add_batch_valid_data_missing_text(ai, database, invalid_batch_data_missing_text):
    """
    @ai.add_batch()
    Tests inserting invalid data.
    Tests for assertion error, summary or description
    must be a non-empty string.
    """
    await database.setup_database(reset=True)
    ai.users = set()

    user_id = 1
    data = {
        'user_id': user_id,
        'data': invalid_batch_data_missing_text
    }
    try:
        await ai.add_batch(**data)
        assert False
    except AssertionError:
        assert True

@pytest.mark.asyncio
async def test_add_batch_duplicate_key(ai, database, duplicate_id_batch_data):
    """
    @ai.add_batch()
    Tests inserting invalid data.
    Tests for assertion error, summary or description
    must be a non-empty string.
    """
    await database.setup_database(reset=True)
    ai.users = set()

    user_id = 1
    data = {
        'user_id': user_id,
        'data': duplicate_id_batch_data
    }

    status, message = await ai.add_batch(**data)
    assert status == BCJStatus.BAD_REQUEST and \
        message == Message.DUPLICATE_ID_BATCH

##################################
### ai.delete_batch() ############
##################################

@pytest.mark.asyncio
async def test_remove_batch_no_updates(ai, database,valid_batch_data):
    """
    @ai.remove_batch()
    Tests:
        Removing a non-existing batch
    """
    await database.setup_database(reset=True)
    ai.users = set()
    user = 1

    #valid_data has batch_id=1
    data = {
        'user_id': 1,
        'data': valid_batch_data
    }
    await ai.add_batch(**data)

    status, message = await ai.remove_batch(user_id=user,batch_id=2)
    assert status == BCJStatus.ERROR and \
        message == Message.NO_DELETION


@pytest.mark.asyncio
async def test_remove_batch_valid_remove(ai, database,valid_batch_data):
    """
    @ai.remove_batch()
    Tests:
        removing an existing batch
    """
    await database.setup_database(reset=True)
    ai.users = set()
    user = 1

    #valid_data has batch_id=1
    data = {
        'user_id': 1,
        'data': valid_batch_data
    }
    await ai.add_batch(**data)

    status, message = await ai.remove_batch(user_id=user,batch_id=1)
    assert status == BCJStatus.OK and \
        message == Message.VALID_INPUT

#############################################
### KDTree and Database cohesion ############
#############################################

@pytest.mark.asyncio
async def test_db_and_kdtree_equivalency_on_delete(ai,valid_batch_data,database,N):
    """
    Tests for KDTree and database cohesion

    Tests
        - Adding a batch of data
        -removing bugs
        -removing a batch
        - empty database
    """
    await database.setup_database(reset=True)
    ai.users = set()
    user = 1
    data = {
        'user_id': user,
        'data': valid_batch_data
    }
    #add a batch and assert that kdtree and database contains same data.
    await ai.add_batch(**data)
    db_data = database.fetch_all(user)
    db_ids = [data['id'] for data in db_data]
    db_embeddings = []
    db_embeddings = [data['embeddings'] for data in db_data]
    kdtree_ids = ai.kdtree.local_indices.tolist()
    kdtree_embeddings = ai.kdtree.data.tolist()
    assert kdtree_embeddings == db_embeddings and db_ids == kdtree_ids

    #delete values and assert that kdtree and database contain the same data
    for i in range(N):
        await ai.remove_bug(user_id=user, id=i)
        db_data = database.fetch_all(user)
        kdtree_ids = ai.kdtree.local_indices.tolist()
        kdtree_embeddings = ai.kdtree.data.tolist()
        db_ids = [data['id'] for data in db_data]
        db_embeddings = [data['embeddings'] for data in db_data]
        assert kdtree_embeddings == db_embeddings and db_ids == kdtree_ids

    #remove everything this user has put in, the batch with batch_id = 1.
    await ai.remove_batch(user_id= user,batch_id=1)
    try:
        await database.fetch_all(user)
        assert False
    except NotFoundError:
        assert ai.kdtree is None

@pytest.mark.asyncio
async def test_kdtree_and_db_equivalency_multiple_users(ai,database):
    """
    KDtree and db cohesion
    Test fetching the correct data for a user.
    """
    await database.setup_database(reset=True)
    ai.users = set()

    ##
    first_user = 1
    for _id in range(2):
        await ai.add_bug(user_id= first_user,
                    structured_info= {
                        'id': _id,
                    },
                    summary='summary',
                    description='description'
        )
    second_user = 2
    await ai.add_bug(user_id= second_user,
                    structured_info= {
                        'id': 1,
                    },
                    summary='summary',
                    description='description'
        )

    db_data = await database.fetch_all(second_user)
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


@pytest.mark.asyncio
async def test_kdtree_and_db_equivalency_update_bug(ai,database):
    """
    KDtree and db cohesion
    Test fetching the correct data for a user.
    """
    await database.setup_database(reset=True)
    ai.users = set()


    user = 1

    await ai.add_bug(user_id= user,
                structured_info= {
                    'id': 1,
                },
                summary='summary',
                description='description'
    )

    await ai.update_bug(user_id= user,
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
