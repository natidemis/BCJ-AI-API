""" Global fixtures """

import pytest
from db import Database
from bcj_ai import BCJAIapi
import numpy as np

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
def rng():
    """ Return default random generator """
    return np.random.default_rng()