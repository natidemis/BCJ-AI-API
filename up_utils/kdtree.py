# -*- coding: utf-8 -*-
"""
June 11

@author: kra33
"""

import logging
import itertools

import numpy as np
import scipy


class KDTreeUP(scipy.spatial.KDTree):
    """
    k-D tree for UP implementing KDTree with euclidean distance sorting.
    For cosine similarity sorting, a specialized data structure must be
    developed.

    Methods:
    __init__
    query

    Instance variables:
    kd_tree
    indexer
    """

    kd_tree = None
    # self.indexer is a dict with tree_index -> data_frame_index
    # mappings
    indexer = None

    def __init__(
            self,
            data,
            *args,
            indices=None,
            **kwargs):

        logging.info("Initializing k-D tree...")
        # Create k-D tree of encoded bugs
        super().__init__(data, *args, **kwargs)
        # Ensure indices are valid
        if indices is None:
            logging.info("Indices are not given. "
                         "Setting indices to 0, 1, ..., %d", len(data))
            indices = range(len(data))
        else:
            assert len(data) == len(indices), \
                "Number of indices must be equal to the number of datapoints"
        # Save mapping from k-D tree indices to bug IDs
        self.local_indices = indices
        self.indexer = dict(zip(itertools.count(), indices))
        logging.info("Done initalizing k-D tree")

    def __map_indices(self, indices):
        """ Map any-shaped array of indices to bug-IDs """
        if isinstance(indices, (list, np.ndarray)):
            return [self.__map_indices(index) for index in indices]
        return self.indexer[indices]

    def query(self, *args, **kwargs):  # pylint: disable=signature-differs
        """ Return bug ID and distance of k nearest encoded bug(s) """
        tree_result = super().query(*args, **kwargs)
        return (tree_result[0], self.__map_indices(tree_result[1]))

    def query_ball_point(self, *args, **kwargs):  # pylint: disable=signature-differs
        """ Return bug ID and distance of bugs within r """
        tree_result = super().query_ball_point(*args, **kwargs)
        return self.__map_indices(tree_result)

    def update(self, new_vector, new_id):
        """ Update the KDTree with a new instance of itself """
        self.__init__(data=np.vstack((super().data, new_vector)),
                      indices=np.append(self.local_indices, new_id))

    def remove(self, bug):
        """ Remove `bug` from k-D tree """
