# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=W0703
# pylint: disable=W0613
"""
@authors: kra33, Gitcelo, natidemis
May 2021

API module for Bug Consolidation for Jira (BCJ) AI model.
Used to store bugs and classify them.
"""

from enum import IntEnum
import os
from threading import Lock
from typing import Tuple, Union
import tensorflow as tf
import numpy as np
from dotenv import load_dotenv
from up_utils.word2vec import Word2Vec
from up_utils.kdtree import KDTreeUP as KDTree
from db import Database, NotFoundError,DuplicateKeyError,MissingArgumentError
from helper import Message
from log import logger
from users import authenticate_user, get_or_create_user

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
        try:
            self.users = set(self.database.fetch_users())
        except NotFoundError:
            self.users = set()
        self.kdtree = None
        self.current_user = None
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


    @staticmethod
    def _restructure_tree(new_data: list) -> KDTree:
        """
        Private method for updating the tree.

        Returns
        -------
        KDTreeUP(KDTree)
        """
        if new_data:
            embeddings = np.vstack([data['embeddings'] for data in new_data])
            ids = np.array([data['id'] for data in new_data])
            return KDTree(data=embeddings, indices=ids)
        return None


    def update_tree_for_user(self, user_id: int) -> None:
        """
        Update the kdtree with the data provided by `user_id`

        Returns
        -------
        None
        """
        try:
            data = self.database.fetch_all(user_id)
            self.kdtree = self._restructure_tree(data)
        except NotFoundError:
            self.kdtree = None
        finally:
            self.current_user = user_id


    @authenticate_user
    def get_similar_bugs_k(self,
                            user_id: int,
                            data: str,
                            structured_info: str=None,
                            k: int=5) -> Tuple[BCJStatus, Union[dict,str]]:
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

        N = len(self.kdtree.indices)
        k = min(k,N)

        try:
            vec= self.model.predict(np.array([self.w2v.get_sentence_matrix(data)]))
        except Exception:
            logger.error('Data is invalid.')
            return BCJStatus.NOT_FOUND, Message.INVALID.value

        with self. __lock:
            result = self.kdtree.query(vec, k=k)
            ids = result[1][0]
            dists = result[0][0]
            #ef up_utils brach(list_for_list_of_lists) verður sameinaður
            #ids = result[1].tolist()
            #dists = result[0].tolist()

        ids = list(map(int,ids)) if k>1 else [int(ids)]
        dists = dists.tolist() if k>1 else [float(dists)]


        response = {
            "id": ids,
            "dist": dists
        }

        return BCJStatus.OK, response

    @get_or_create_user
    def add_bug(self,
                user_id: int,
                structured_info: dict,
                summary: str=None,
                description: str=None) -> Tuple[BCJStatus, Message]:
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
        try:
            embeddings= self.model.predict(np.array([self.w2v.get_sentence_matrix(data)]))
        except Exception:
            logger.error('Data is invalid.')
            return BCJStatus.NOT_FOUND, Message.INVALID

        with self.__lock:
            try:
                self.database.insert(_id=structured_info['id'],
                            user_id=user_id,
                            embeddings=embeddings,
                            batch_id=batch_id)
            except(TypeError,NotFoundError,DuplicateKeyError):
                return BCJStatus.ERROR, Message.INVALID_ID_OR_DATE

        with self.__lock:
            if self.kdtree is None:
                self.kdtree = KDTree(data=embeddings, indices=[structured_info['id']])
            else:
                self.kdtree.update(embeddings, structured_info['id'])
        return BCJStatus.OK, Message.VALID_INPUT

    @authenticate_user
    def remove_bug(self, _id: int, user_id: int) -> Tuple[BCJStatus, Message]:
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
                self.database.delete(_id,user_id)
            except NoUpdatesError:
                return BCJStatus.NOT_FOUND, Message.VALID_INPUT
            self.update_tree_for_user(user_id)
        return BCJStatus.OK, Message.VALID_INPUT

    @authenticate_user
    def update_bug(self,
                    user_id: int,
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
        batch_id = structured_info['batch_id'] if \
                        'batch_id' in structured_info else None

        if not(bool(summary) and bool(description)):
            with self.__lock:
                try:
                    self.database.update(_id=structured_info['id'],
                                    user_id=user_id,
                                    batch_id=batch_id)
                    return BCJStatus.OK, Message.VALID_INPUT
                except Exception:
                    return BCJStatus.NOT_FOUND, Message.INVALID_ID_OR_DATE

        data = description if bool(description) else summary
        try:
            embeddings= self.model.predict(np.array([self.w2v.get_sentence_matrix(data)]))
        except Exception:
            logger.error('Data is invalid.')
            return BCJStatus.NOT_FOUND, Message.INVALID

        with self.__lock:
            try:
                self.database.update(_id=structured_info['id'],
                                user_id=user_id,
                                embeddings=embeddings,
                                batch_id=batch_id)
            except: #vantar að meðhöndla
                return BCJStatus.NOT_FOUND, Message.INVALID_ID_OR_DATE
            self.update_tree_for_user(user_id)
            
        return BCJStatus.OK, Message.VALID_INPUT

    @authenticate_user
    def remove_batch(self, batch_id: int, user_id: int) -> Tuple[BCJStatus, Message]:
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
                self.database.delete_batch(batch_id,user_id)
            except NoUpdatesError: #vantar að meðhöndla
                return BCJStatus.ERROR, Message.INVALID
            self.update_tree_for_user(user_id)

        return BCJStatus.OK, Message.VALID_INPUT

    @get_or_create_user
    def add_batch(self, batch: list, user_id: int) -> Tuple[BCJStatus, Message]:
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
        embeddings = self.model.predict(np.array(self.w2v.get_sentence_matrix(sentences)))
        batch_data = [(bug['id'],user_id,embedding,bug['batch_id'])
                            for bug, embedding in zip(batch, embeddings)]
        with self.__lock:
            try:
                self.database.insert_batch(batch_data)
            except (TypeError, MissingArgumentError,NotFoundError, DuplicateKeyError):
                return BCJStatus.ERROR, Message.INVALID
            self.update_tree_for_user(user_id)
        return BCJStatus.OK, Message.VALID_INPUT
