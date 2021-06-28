# -*- coding: utf-8 -*-
"""
@authors: kra33, Gitcelo, natidemis
May 2021

API module for Bug Consolidation for Jira (BCJ) AI model. 
Used to store bugs and classify them.
"""

import random
from enum import IntEnum
import tensorflow as tf
from up_utils.word2vec import Word2Vec
from up_utils.kdtree import KDTreeUP as KDTree
import numpy as np
from db import Database
from threading import Lock

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
        """
        self.__lock = Lock()
        self.db = Database()
        self.model = tf.keras.models.load_model('Models', compile=False)
        self.w2v = Word2Vec(
            wv_path='wordvectors.wv',
            dataset='googlenews',
            googlenews_path='./GoogleNews-vectors-negative300.bin')
        prev_data = self.db.fetch_all()
        if prev_data:
            vec = np.vstack([data['summary'] for data in prev_data])
            ids = np.array([data['id'] for data in prev_data])
            self.kdtree = KDTree(data=vec, indices=ids)
        else:
            self.kdtree = None

        
    
    def get_similar_bugs_k(self, summary: str=None, description: str=None, structured_info: str=None, k: int=5):
        """
        Return the ID of the k most similar bugs based on given summary, desription, and
        structured information.

        Returns
        -------
        status : BCJStatus
            OK if the requested number of bugs were found.
        idx : list
            A list of min(k,N) most similar bugs where N is the total number of bugs
        """
        if self.kdtree is None:
            return BCJStatus.NOT_FOUND, 'No examples available'
        if not(bool(summary) or bool(description) or bool(structured_info)):
            return BCJStatus.NOT_FOUND, 'At least one of the parameters summary, description, or structured_info must be filled'
        data = description if description is not None else summary #sækjum annað hvort description eða summary
        vec = self.model.predict(np.array([self.w2v.get_sentence_matrix(data)])) #sækjum vigur á annar hvor þeirra
        result = self.kdtree.query(vec, k=k)
        return BCJStatus.OK, result

    def get_similar_bugs_threshold(self, summary: str=None, description: str=None, structured_info: dict=None, threshold: str=0.5) -> BCJStatus and (list or str):
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
        if self.kdtree is None:
            return BCJStatus.NOT_FOUND, 'No examples available'
        return BCJStatus.OK, [random.randint(1,1000) for _ in range(k)]

    def add_bug(self, summary: str=None, description: str=None, structured_info: dict=None) -> BCJStatus: 
        """
        Add a bug with given summary, description and structured information. Here it is assumed that all the data
        has already been validated and sanitized. To see how we sanitized the data, see __init__.py in the folder
        app.

        Returns
        -------
        status: BCJStatus
            OK if the bug insertion is successful
            ERROR if the bug insertion is unsuccessful
        """
        if not (bool(summary) or bool(description) or bool(structured_info)):
            return BCJStatus.ERROR
        #-----------------------------------------------------------------------------
        # summary og description eiga að vera vigrar í gagnagrunninum, ekki texti!!!
        # Geymum all vigra undir 'summary' á meðan við getum bara sett inn einn vigur.
        #-----------------------------------------------------------------------------
       
        data = description if description is not None else summary # Sækjum annað hvort description eða summary
        bucket = structured_info['bucket'] if 'bucket' in structured_info else None # Bucket er optional
        vec = self.model.predict(np.array([self.w2v.get_sentence_matrix(data)])) # Sækjum vigur á annar hvor þeirra
        new_id = structured_info['id']
        self.__lock.acquire()
        if self.kdtree is None:
            self.kdtree = KDTree(data=vec, indices=new_id)
        else:
            self.kdtree.update(vec, new_id)
        res = self.db.insert(id=new_id,
                        date=structured_info['date'],
                        summary=vec, 
                        bucket=bucket)
        self.__lock.release()
        if res:
            return BCJStatus.OK
        else:
            return BCJStatus.ERROR


    def remove_bug(self, idx: str) -> BCJStatus:
        """
        Remove a bug with idx as its id.
        
        Returns
        -------
        status: BCJstatus
            OK if bug removal is successful
            ERRROR if bug removal is unsuccessful
        """
        
        
        return BCJStatus.OK

    def update_bug(self, summary: str=None, description: str=None, structured_info: str=None) -> BCJStatus:
        """
        Updates a bug with the parameters given. The id of the bug should be in structured_info.
        
        Returns
        -------
        status: BCJStatus
            OK if bug update is successful
            ERROR if bug update is unsuccessful
        """
        if not(bool(summary) or bool(description) or bool(structured_info)):
            return BCJStatus.ERROR
        return BCJStatus.OK
    
    def get_batch_by_id(self, idx: str) -> [BCJStatus,int]:
        """
        Returns a specific batch of bugs. The batch's id is idx.
        """
        return BCJStatus.OK, idx
    
    def remove_batch(self, idx: str) -> BCJStatus:
        """
        Removes a batch of bugs. The batch's id is idx.
        """
        self.__lock.acquire()
        self.db.delete_bucket(idx) #vitum ekki hvort við fjarlægðum úr gagnagrunninum
        prev_data = self.db.fetch_all()
        if prev_data:
            vec = np.vstack([data['summary'] for data in prev_data])
            ids = np.array([data['id'] for data in prev_data])
            self.kdtree = KDTree(data=vec, indices=ids)
        else:
            self.kdtree = None
        self.__lock.release()
        return BCJStatus.OK