# -*- coding: utf-8 -*-

"""
@author kra33
April 2021

Test module for testing k-D tree in `testing.py`
"""


import pytest
import numpy as np

import config # pylint: disable=import-error
from up_utils.kdtree import KDTreeUP # pylint: disable=import-error

# pylint: disable=redefined-outer-name


################
### FIXTURES ###
################

@pytest.fixture
def rng():
    """ Return default random generatotr """
    return np.random.default_rng()

@pytest.fixture
def test_data(rng):
    """ Return random test data, but the same for every call in a session """
    return rng.random(config.pytest.EMBEDDING_SHAPE)

@pytest.fixture
def test_labels(rng):
    """ Return random test data, but the same for every call in a session """
    return rng.integers(low=1,
                        high=config.pytest.N_CLASSES,
                        size=config.pytest.N_SAMPLES)


@pytest.fixture
def kdtree_labeled(test_data, test_labels):
    """ Return a UP flavored k-D tree, using `test_data` """
    return KDTreeUP(test_data, indices=test_labels)


@pytest.fixture
def kdtree_unlabeled(test_data):
    """ Return a UP flavored k-D tree, using `test_data` """
    return KDTreeUP(test_data)


@pytest.fixture
def kdtree(kdtree_unlabeled):
    """ Return a UP flavored k-D tree, using `test_data` """
    return kdtree_unlabeled


###################
### TEST KDTREE ###
###################
def test_kdtree_create(kdtree):
    """ Test creation of UP flavored k-D tree """
    assert kdtree is not None

def test_kdtree_query_labeled(kdtree_labeled, test_data, test_labels):
    """ Test querying of UP flavored k-D tree """
    for point, idx, label in zip(test_data,
                                 range(len(test_data)),
                                 test_labels):
        # The close_points are IDs of points
        distances, ids = kdtree_labeled.query(point, k=10)
        closest_point = ids[0]

        assert distances[0] == 0 # Closest point is 0-distance
        assert np.isclose(test_data[idx], point).all()
        assert closest_point == label

def test_kdtree_query_unlabeled(kdtree_unlabeled, test_data):
    """ Test querying of UP flavored k-D tree """
    for point in test_data:
        # The close_points are IDs of points
        distances, ids = kdtree_unlabeled.query(point, k=10)
        closest_point = ids[0]

        assert distances[0] == 0 # Closest point is 0-distance
        assert np.isclose(test_data[closest_point], point).all()

def test_kdtree_query_ball_point(kdtree, test_data):
    """ Test querying ball point of UP flavored k-D tree """
    for point in test_data:
        # The close_points are IDs of points
        nearest_neighbors = kdtree.query_ball_point(
            point,
            r=config.pytest.KDTREE_QUERY_DISTANCE,
        )
        closest_point = nearest_neighbors[0]

        assert np.isclose(test_data[closest_point], point).all()


def test_kdtree_base_rate(kdtree_labeled, test_data, test_labels):
    """ Test the base rate of uniformly random data """
    top_count = np.array([0 for _ in range(config.pytest.KDTREE_TOP_K)])
    for datum, label in zip(test_data, test_labels):
        nearest = kdtree_labeled.query(datum, k=len(top_count))[-1]
        if len(nearest) > 1 and label in nearest[1:]:
            top_count[nearest.index(label)] += 1
    # Integrate and normalize
    for i in range(len(top_count)-1):
        top_count[i+1] += top_count[i]
        top_count[i] /= len(test_data)
    top_count[-1] /= len(test_data)

    expected_upper_bound = np.array([-2/(x+3)+1
                                     for x in range(len(top_count))])
    expected_lower_bound = np.array([0 for x in range(len(top_count))])

    assert (top_count < expected_upper_bound).all()
    assert (top_count > expected_lower_bound).all()
