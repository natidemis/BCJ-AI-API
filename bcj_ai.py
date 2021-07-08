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
import os
from dotenv import load_dotenv

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
        load_dotenv()
        OUTPUT_FILE = os.getenv('OUTPUT_FILE')
        DATASET = os.getenv('DATASET') # Dataset can either be googlenews or commoncrawl
        COMMONCRAWL_PATH = os.getenv('COMMONCRAWL_PATH')
        GOOGLENEWS_PATH = os.getenv('GOOGLENEWS_PATH')
        self.w2v = Word2Vec(
            outputfile=OUTPUT_FILE,
            wv_path='wordvectors.wv',
            dataset=DATASET,
            commoncrawl_path=COMMONCRAWL_PATH,
            googlenews_path=GOOGLENEWS_PATH)
        prev_data = self.db.fetch_all()
        self.kdtree = self.__update_tree(prev_data)

    
    def __update_tree(self,prev_data: list) -> KDTree:
        """
        Private method for updating the tree.
        
        Returns
        -------
        KDTreeUP(KDTree)
        """
        if prev_data:
            vec = np.vstack([data['summary'] for data in prev_data])
            ids = np.array([data['id'] for data in prev_data])
            return KDTree(data=vec, indices=ids)
        else:
            return None     
    
    def get_similar_bugs_k(self,
                            summary: str=None,
                            description: str=None,
                            structured_info: str=None,
                            k: int=5):
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
        N = len(self.kdtree.indices)
        if k>N:
            k=N
        data = description if bool(description) else summary #sækjum annað hvort description eða summary
        vec = self.model.predict(np.array([self.w2v.get_sentence_matrix(data)])) #sækjum vigur á annar hvor þeirra
        self.__lock.acquire()
        result = self.kdtree.query(vec, k=k)
        self.__lock.release()
        response = {
            "id": result[1],
            "dist": result[0].tolist()
        }
        return BCJStatus.OK, response

    def get_similar_bugs_threshold(self,
                                summary: str=None,
                                description: str=None,
                                structured_info: dict=None,
                                threshold: str=0.5) -> BCJStatus and (list or str):
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

    def add_bug(self,
                summary: str=None,
                description: str=None,
                structured_info: dict=None) -> BCJStatus: 
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


        data = description if bool(description) else summary # Sækjum annað hvort description eða summary
        batch_id = structured_info['batch_id'] if 'batch_id' in structured_info else None # Bucket er optional
        vec = self.model.predict(np.array([self.w2v.get_sentence_matrix(data)])) # Sækjum vigur á annar hvor þeirra
        new_id = structured_info['id']
        self.__lock.acquire()
        try:
            self.db.insert(id=new_id,
                        date=structured_info['date'],
                        summary=vec, 
                        batch_id=batch_id)
        except:
            self.__lock.release()
            return BCJStatus.ERROR

        if self.kdtree is None:
            self.kdtree = KDTree(data=vec, indices=[new_id])
        else:
            self.kdtree.update(vec, new_id)
        
        self.__lock.release()
        return BCJStatus.OK


    def remove_bug(self, idx: int) -> BCJStatus:
        """
        Remove a bug with idx as its id.
        
        Returns
        -------
        status: BCJstatus
            OK if bug removal is successful
            ERRROR if bug removal is unsuccessful
        """
        try:
            self.__lock.acquire()
            rows = self.db.delete(idx)
            if rows > 0:
                prev_data = self.db.fetch_all()
                self.kdtree = self.__update_tree(prev_data)
            self.__lock.release()
        except:
            self.__lock.release()
            return BCJStatus.ERROR
        
        return BCJStatus.OK

    def update_bug(self,
                    summary: str=None,
                    description: str=None,
                    structured_info: str=None) -> BCJStatus:
        """
        Updates a bug with the parameters given. The id of the bug should be in structured_info.
        
        Returns
        -------
        status: BCJStatus
            OK if bug update is successful
            ERROR if bug update is unsuccessful
        """
        
        #Gætum þurft að breyta ef 'DATE' þarf að fara í gervigreindina
        if not(bool(summary) and bool(description)):
            try:
                batch_id = structured_info['batch_id'] if 'batch_id' in structured_info else None
                self.__lock.acquire()
                self.db.update(id=structured_info['id'],date=structured_info['date'],batch_id=batch_id)
                self.__lock.release()
                return BCJStatus.OK
            except:
                self.__lock.release()
                return BCJStatus.ERROR

        data = description if bool(description) else summary
        vec = self.model.predict(np.array([self.w2v.get_sentence_matrix(data)]))
        try:
            self.lock.acquire()
            self.db.update(id=structured_info['id'],date=structured_info['date'],summary=vec,batch_id=batch_id)
            prev_data = self.db.fetch_all()
            self.kdtree = self.__update_tree(prev_data)
            self.__lock.release()
        except:
            self.__lock.release()
            return BCJStatus.ERROR
        return BCJStatus.OK
    
    def get_batch_by_id(self, idx: int) -> [BCJStatus,int]: #Ólíklegt að þetta verði notað
        """
        Returns a specific batch of bugs. The batch's id is idx.

        Returns
        -------
        status: BCJStatus
            OK if bug update is successful
            ERROR if bug update is unsuccessful
        """
        return BCJStatus.OK, idx
    
    def remove_batch(self, idx: int) -> BCJStatus:
        """
        Removes a batch of bugs. The batch's id is idx.

        Returns
        -------
        status: BCJStatus
            OK if bug update is successful
            ERROR if bug update is unsuccessful
        """
        try:
            self.__lock.acquire()
            num_of_deleted_rows = self.db.delete_batch(idx) #vitum ekki hvort við fjarlægðum úr gagnagrunninum
            if num_of_deleted_rows > 0:
                prev_data = self.db.fetch_all()
                self.kdtree = self.__update_tree(prev_data)
            self.__lock.release()
        except:
            self.__lock.release()
            return BCJStatus.ERROR
        return BCJStatus.OK

    
    def add_batch(self, batch: list) -> BCJStatus:
        """
        Adds a batch to the database and updates the KD-Tree

        Returns
        -------
        BCJStatus
        """
        
        vectored_batch = []
        for bug in batch:
            data = bug['description'] if bool(bug['description']) else bug['summary'] # Sækjum annað hvort description eða summary
            vec = self.model.predict(np.array([self.w2v.get_sentence_matrix(data)])) # Sækjum vigur fyri desc eða summ
            vectored_batch.append((
                bug['id'],
                vec,
                None,
                bug['batch_id'],
                bug['date']
            ))
        try:
            self.__lock.acquire()
            self.db.insert_batch(vectored_batch)
            self.__lock.release()
        except:
            self.lock.release()
            return BCJStatus.ERROR

        self.__lock.acquire()
        updated_results = self.db.fetch_all()
        self.kdtree = self.__update_tree(updated_results)
        self.__lock.release()
        return BCJStatus.OK