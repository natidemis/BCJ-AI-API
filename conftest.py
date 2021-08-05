""" Global fixtures """

import pytest
import numpy as np
import asyncio
from Misc.db import Database
from bcj_ai import BCJAIapi


@pytest.fixture
@pytest.mark.asyncio
async def ai():
    """
    Class to be tested
    """
    return await BCJAIapi()

@pytest.fixture
def N():
    """
    Arbitrary value high enough to test multiple cases
    """
    return 30


@pytest.fixture
def rng():
    """ Return default random generator """
    return np.random.default_rng()

@pytest.fixture(scope='module')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()