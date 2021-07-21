"""
@author Gitcelo
July 2021

Test module for testing functions in `bcj_ai.py`
"""

import pytest
import numpy as np

from bcj_ai import BCJAIapi

################
### FIXTURES ###
################

@pytest.fixture
def ai():
    return BCJAIapi()

###################
### TEST KDTREE ###
###################

