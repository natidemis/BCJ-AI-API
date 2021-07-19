# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=W0703
"""
@authors: kra33, Gitcelo, natidemis
May 2021

API module for Bug Consolidation for Jira (BCJ) AI model.
Used to store bugs and classify them.
"""

from enum import IntEnum
import os
from threading import Lock
from typing import Tuple
import tensorflow as tf
import numpy as np
from dotenv import load_dotenv
from up_utils.word2vec import Word2Vec
from up_utils.kdtree import KDTreeUP as KDTree
from db import Database
from helper import Message


class BCJStatus(IntEnum):
    """
    Class that contains status codes
    """
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
        self.database = Database()
        self.model = tf.keras.models.load_model('Models', compile=False)
        load_dotenv()
        OUTPUT_FILE = os.getenv('OUTPUT_FILE')
        DATASET = os.getenv('DATASET') # Dataset can either be googlenews or commoncrawl
        COMMONCRAWL_PATH = os.getenv('COMMONCRAWL_PATH')
        GOOGLENEWS_PATH = os.getenv('GOOGLENEWS_PATH')
        WV_ITEM_LIMIT = os.getenv('WV_ITEM_LIMIT')
        self.w2v = Word2Vec(
            outputfile=OUTPUT_FILE,
            dataset=DATASET,
            commoncrawl_path=COMMONCRAWL_PATH,
            googlenews_path=GOOGLENEWS_PATH,
            wv_item_limit=WV_ITEM_LIMIT)
        prev_data = self.database.fetch_all()
        self.kdtree = self.__update_tree(prev_data)

    @staticmethod
    def __update_tree(prev_data: list) -> KDTree:
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
        return None

    def get_similar_bugs_k(self,
                            summary: str=None,
                            description: str=None,
                            structured_info: str=None,
                            k: int=5) -> Tuple[BCJStatus, dict]:
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
            return BCJStatus.NOT_FOUND, \
                '''At least one of the parameters summary,
                description, or structured_info must be filled'''
        N = len(self.kdtree.indices)
        k = min(k,N)
        data = description if bool(description) else summary
        vec = self.model.predict(np.array([self.w2v.get_sentence_matrix(data)]))
        with self. __lock:
            result = self.kdtree.query(vec, k=k)
            ids = result[1][0]
            dists = result[0][0]

        ids = list(map(int,ids)) if k>1 else [int(ids)]
        dists = dists.tolist() if k>1 else [float(dists)]


        response = {
            "id": ids,
            "dist": dists
        }

        return BCJStatus.OK, response

    def add_bug(self,
                structured_info: dict,
                summary: str=None,
                description: str=None) -> Tuple[BCJstatus, Message]:
        """
        Add a bug with given summary, description and structured information.
        Here it is assumed that all the data
        has already been validated and sanitized.
        To see how we sanitized the data, see __init__.py in the folder
        app.

        Returns
        -------
        status: BCJStatus
            OK if the bug insertion is successful
            ERROR if the bug insertion is unsuccessful
        """


        data = description if bool(description) else summary
        batch_id = structured_info['batch_id'] if 'batch_id' in structured_info else None
        vec = self.model.predict(np.array([self.w2v.get_sentence_matrix(data)]))
        new_id = structured_info['id']

        with self.__lock:
            try:
                self.database.insert(_id=new_id,
                            date=structured_info['date'],
                            summary=vec,
                            batch__id=batch_id)
            except Exception:
                return BCJStatus.ERROR, Message.INVALID_ID_OR_DATE

        with self.__lock:
            if self.kdtree is None:
                self.kdtree = KDTree(data=vec, indices=[new_id])
            else:
                self.kdtree.update(vec, new_id)
        return BCJStatus.OK, Message.VALID_INPUT

    def remove_bug(self, idx: int) -> Tuple[BCJStatus,Message]:
        """
        Remove a bug with idx as its id.

        Returns
        -------
        status: BCJstatus
            OK if bug removal is successful
            ERRROR if bug removal is unsuccessful
        """
        with self.__lock:
            try:
                rows = self.database.delete(idx)
                if rows > 0:
                    prev_data = self.database.fetch_all()
                    self.kdtree = self.__update_tree(prev_data)
            except Exception:
                return BCJStatus.ERROR, Message.INVALID
        return BCJStatus.OK, Message.VALID_INPUT

    def update_bug(self,
                    structured_info: dict,
                    summary: str=None,
                    description: str=None) -> Tuple[BCJStatus, Message]:
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
            with self.__lock:
                try:
                    batch_id = structured_info['batch_id'] if \
                        'batch_id' in structured_info else None
                    self.database.update(_id=structured_info['id'],
                                    date=structured_info['date'],
                                    batch__id=batch_id)
                    return BCJStatus.OK, Message.VALID_INPUT
                except Exception:
                    return BCJStatus.ERROR, Message.INVALID_ID_OR_DATE

        data = description if bool(description) else summary
        vec = self.model.predict(np.array([self.w2v.get_sentence_matrix(data)]))
        with self.__lock:
            try:
                self.database.update(_id=structured_info['id'],
                                date=structured_info['date'],
                                summary=vec,
                                batch__id=batch_id)
                prev_data = self.database.fetch_all()
                self.kdtree = self.__update_tree(prev_data)
            except Exception:
                return BCJStatus.ERROR, Message.INVALID_ID_OR_DATE
        return BCJStatus.OK, Message.VALID_INPUT

    def remove_batch(self, idx: int) -> Tuple[BCJstatus, Message]:
        """
        Removes a batch of bugs. The batch's id is idx.

        Returns
        -------
        status: BCJStatus
            OK if bug update is successful
            ERROR if bug update is unsuccessful
        """
        with self.__lock:
            try:
                #vitum ekki hvort við fjarlægðum úr gagnagrunninum
                num_of_deleted_rows = self.database.delete_batch(idx)
                if num_of_deleted_rows > 0:
                    prev_data = self.database.fetch_all()
                    self.kdtree = self.__update_tree(prev_data)
            except Exception:
                return BCJStatus.ERROR, Message.INVALID
        return BCJStatus.OK, Message.VALID_INPUT


    def add_batch(self, batch: list) -> Tuple[BCJStatus, Message]:
        """
        Adds a batch to the database and updates the KD-Tree

        Returns
        -------
        BCJStatus
        """

        sentences = []
        for bug in batch:
            sentence = bug['description'] if bool(bug['description']) else bug['summary']
            sentences.append(sentence)
        vectorized_sentences = self.model.predict(np.array(self.w2v.get_sentence_matrix(sentences)))
        vectored_batch = [(bug['id'],vec,None,bug['batch_id'],bug['date'])
                            for bug, vec in zip(batch, vectorized_sentences)]
        with self.__lock:
            try:
                self.database.insert_batch(vectored_batch)
            except Exception:
                return BCJStatus.ERROR, Message.INVALID
            updated_results = self.database.fetch_all()
            self.kdtree = self.__update_tree(updated_results)
        return BCJStatus.OK, Message.VALID_INPUT
