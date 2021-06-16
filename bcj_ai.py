# -*- coding: utf-8 -*-
"""
@author: kra33
May 2021

API module for Bug Consolidation for Jira (BCJ) AI model
"""

import random
from enum import IntEnum
import tensorflow as tf
from up_utils.word2vec import Word2Vec
from up_utils.kdtree import KDTreeUP as KDTree
import numpy as np

class BCJStatus(IntEnum):
    OK = 200
    NOT_FOUND = 404
    ERROR = 500

class BCJAIapi:
    """
    API class for AI
    """

    def __init__(self):
        """
        Initialize the AI model from disk; read embedding vectors from disk;
        get ready for classifying bugs and returning similar bug ids.

        Returns
        -------
        ai : BCJAIapi
            An instance of the api for querying the AI
        """
        self.model = tf.keras.models.load_model('Models', compile=False)
        kdt = None
        self.w2v = Word2Vec(wv_path='wordvectors.wv', dataset='googlenews', googlenews_path='./google_news.bin')
    
    def get_similar_bugs_k(self, summary: str=None, description: str=None, structured_info: str=None, k: int=5):
        """
        Return the ID of the `k` most similar bugs based on given summary, desription, and
        structured information.

        Returns
        -------
        status : BCJStatus
            OK if the requested number of bugs were found.
            ERROR if less than k bugs were found.
        idx : list
            A list of `min(k,N)` most similar bugs where N is the total number of bugs
        """
        bugs = [random.randint(1,1000) for _ in range(k)]
        if not(bool(summary) or bool(description) or bool(structured_info)):
            return BCJStatus.NOT_FOUND, 'At least one of the parameters summary, description, or structured_info must be filled'
        summ = self.w2v.get_sentence_matrix(summary)
        arr = np.array([summ])
        assert arr.shape == (1,100,300), 'Ekki eins'
        summ = self.model.predict(arr)
        print(summ)
        #desc = w2v.get_sentence_matrix(description)
        return BCJStatus.OK, bugs

    def get_similar_bugs_threshold(self, summary: str=None, description: str=None, structured_info: dict=None, threshold: str=0.5) -> BCJStatus or list:
        """
        Return the ID of bugs at least `threshold` similar; based on given summary, desription, and
        structured information.

        Returns
        -------
        status : BCJStatus
            OK if the requested number of bugs were found.
            ERROR if less than k bugs were found.
        idx : list
            A list of `min(k,N)` most similar bugs where N is the total number of bugs
        """
        return [random.randint(1,1000) for _ in range(k)]

    def add_bug(self, summary: str=None, description: str=None, structured_info: dict=None) -> BCJStatus: 
        """
        Add a bug with given summary, description and structured information.

        Returns
        -------
        TODO
        """
        if not (bool(summary) or bool(description) or bool(structured_info)):
            return BCJStatus.ERROR
        return BCJStatus.OK

    def remove_bug(self, idx: int) -> BCJStatus:
        """
        """
        return BCJStatus.OK

    def update_bug(self, idx: int, summary: str=None, description: str=None, structured_info: str=None) -> BCJStatus:
        """
        """
        if not(bool(summary) or bool(description) or bool(structured_info)):
            return BCJStatus.ERROR
        return BCJStatus.OK
    
    def get_batch_by_id(self, idx: int) -> [BCJStatus,int]:
        return BCJStatus.OK, idx
    
    def remove_batch(self, idx: int) -> BCJStatus:
        return BCJStatus.OK