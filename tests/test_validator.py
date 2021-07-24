import sys, os
import pytest
import numpy as np
import random
import lorem
import datetime

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

from helper import Validator

################
### FIXTURES ###
################

@pytest.fixture
def validator():
    return Validator()

@pytest.fixture
def get_random_date(year='2015'):

    # try to get a date
    try:
        return datetime.datetime.strptime('{} {}'.format(random.randint(1, 366), year), '%j %Y')

    # if the value happens to be in the leap year range, try again
    except ValueError:
        return get_random_date(year)



@pytest.fixture
def random_valid_data(get_random_date):
    return [{
        "user_id": random.randint(1,1000),
        "summary": lorem.sentence(),
        "description": lorem.paragraph(),
        "structured_info": {
            "id": random.randint(1,1000),
            "date": str(get_random_date)[0:10] 
        }
    } for _ in range(100)]


@pytest.fixture
def validate_data_get_test_data(get_random_date):
    return [{
        "user_id": random.randint(1,1000),
        "summary": lorem.sentence(),
        "description": lorem.paragraph(),
        "structured_info": {
            "date": str(get_random_date)[0:10]
        },
        **({'k': random.randint(1,10)} if \
                bool(random.getrandbits(1)) else {} )
    } for _ in range(100)]


@pytest.fixture
def validate_data_get_test_data_negative_k(get_random_date):
    return [{
        "user_id": random.randint(1,1000),
        "summary": lorem.sentence(),
        "description": lorem.paragraph(),
        "structured_info": {
            "date": str(get_random_date)[0:10]
        },
        'k': random.randint(-10,-1)
    } for _ in range(100)]

@pytest.fixture
def random_valid_update_data(get_random_date):
    data = []

    for _ in range(100):
        which = random.choice(["summary","description","both", None])
        if which == 'summary':

            data.append({
                    "user_id": random.randint(1,1000),
                    "summary": lorem.sentence(),
                    "structured_info": {
                        "id": random.randint(1,1000),
                        "date": str(get_random_date)[0:10] 
                        }
                })
        elif which == 'description':
            data.append({
                    "user_id": random.randint(1,1000),
                    "description": lorem.paragraph(),
                    "structured_info": {
                        "id": random.randint(1,1000),
                        "date": str(get_random_date)[0:10] 
                        }
                })
        elif which == 'both':
            data.append({
                    "user_id": random.randint(1,1000),
                    "summary": lorem.sentence(),
                    "description": lorem.paragraph(),
                    "structured_info": {
                        "id": random.randint(1,1000),
                        "date": str(get_random_date)[0:10],
                        "batch_id": 1
                        }
                })
        else:
            data.append({
                    "user_id": random.randint(1,1000),
                    "structured_info": {
                        "id": random.randint(1,1000),
                        "date": str(get_random_date)[0:10],
                        "batch_id": None
                        }
                })

    return data


@pytest.fixture
def data_with_missing_value(get_random_date):
    return [{
        "user_id": random.randint(1,1000),
        "description": lorem.paragraph(),
        "structured_info": {
            "id": random.randint(1,1000),
            "date": str(get_random_date)[0:10] 
        }
    } for _ in range(100)]


@pytest.fixture
def invalid_date_data(get_random_date):
    return [{
        "user_id": random.randint(1,1000),
        "summary": lorem.sentence(),
        "description": lorem.paragraph(),
        "structured_info": {
            "id": random.randint(1,1000),
            "date": random.choice(["2020-30-10","string","2020-02-31", 1]) 
        }
    } for _ in range(100)]

#####################################
### test Validator.validate_data() ###
######################################

def test_validate_data(validator, random_valid_data):
    """
    @Validator.validate_data()
    Test whether correct data format gives any errors
    """
    for data in random_valid_data:
        validator.validate_data(data)

def test_validate_data_incorrect_date(validator, invalid_date_data):
    """
    @Validator.validate_data()

    Test whether invalid date gives any errors
    """
    for data in invalid_date_data:
        try:
            validator.validate_data(data)
            assert False
        except ValueError:
            assert True

def test_validate_data_missing_value(validator, data_with_missing_value):
    """
    @Validator.validate_data()

    Test whether invalid date gives any errors
    """
    for data in data_with_missing_value:
        try:
            validator.validate_data(data)
            assert False
        except ValueError:
            assert True

####################################
### test Validator.update_data() ###
####################################

def test_random_valid_update_data(random_valid_update_data, validator):
    """
    """
    for data in random_valid_update_data:
        validator.validate_update_data(data)

##########################################
### test Validator.validate_data_get() ###
##########################################

def test_validate_data_get(validator, validate_data_get_test_data):
        for data in validate_data_get_test_data:
            validator.validate_data_get(data)


def test_validate_data_get_invalid_k(validator, validate_data_get_test_data_negative_k):
        for data in validate_data_get_test_data_negative_k:
            try:
                validator.validate_data_get(data)
                assert False
            except ValueError:
                assert True
