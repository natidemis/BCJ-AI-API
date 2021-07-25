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
import bleach
from dotenv import load_dotenv
from up_utils.word2vec import Word2Vec
from up_utils.kdtree import KDTreeUP as KDTree
from db import Database, NotFoundError,DuplicateKeyError,MissingArgumentError, NoUpdatesError
from helper import Message
from log import logger



def authenticate_user(fn):
    """
    Method for validating the given user_id.
    If the user exists, fetch data for that 'user' if required.
    Returns
    -------
    Decorator to be applied to a function.
    """
    def decorator(self, *args, **kwargs):
        user_id = kwargs['user_id'] if 'user_id' in kwargs \
            else args[0]
        if user_id in self.users:
            if self.current_user != user_id:
                self.update_tree_for_user(user_id)
            logger.info('User: %s in database: %s. Auth succeeded.',user_id,self.users)
        else:
            logger.error('User: %s not in database: %s, Auth failed',user_id,self.users)
            raise ValueError('User not available')
        return fn(self, *args, **kwargs)
    return decorator

def get_or_create_user(fn):
    """
    Method for validating the given user_id.
    If the user exists, fetch data for that 'user' if required.
    Otherwise, create a new user for the given user_id
    Returns
    -------
    Decorator to be applied to a function.
    """
    def decorator(self, *args, **kwargs):
        user_id = kwargs['user_id'] if 'user_id' in kwargs \
            else args[0]
        if user_id in self.users:
            if self.current_user != user_id:
                self.update_tree_for_user(user_id)
        else:
            try:
                self.database.insert_user(user_id)
            except (TypeError, DuplicateKeyError) as e:
                logger.error('Inserting user: %s failed for err: %s',user_id, e)
                raise e
            self.users.add(user_id)
            self.update_tree_for_user(user_id)
            logger.info('Inserted user: %s, new user set: %s',user_id,self.users)
        logger.info('User: %s, already in: %s',user_id,self.users)
        return fn(self, *args, **kwargs)
    return decorator


class BCJStatus(IntEnum):
    """
    Class that contains status codes
    """
    OK = 200
    NOT_FOUND = 404
    ERROR = 500
    BAD_REQUEST = 400

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
        with self.__lock:
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
                            summary: str = None,
                            description: str = None,
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

        assert bool(summary) or bool(description)

        #prepare data for vectorization and insertion
        data = bleach.clean(description) if bool(description) \
            else bleach.clean(summary)
        if self.kdtree is None:
            return BCJStatus.NOT_FOUND, 'No examples available'

        N = len(self.kdtree.indices)
        k = min(k,N)

        try:
            vec= self.model.predict(np.array([self.w2v.get_sentence_matrix(data)]))
        except Exception:
            logger.error('Data is invalid.')
            return BCJStatus.NOT_FOUND, Message.UNPROCESSABLE_INPUT

        with self. __lock:
            dists,ids = self.kdtree.query(vec, k=k)
        
        response = {
            "id": ids.flatten().tolist(),
            "dist": dists.flatten().tolist()
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
        assert bool(description) or bool(summary)

        #Prepare the data for vectorization and insertion
        data = bleach.clean(description) if bool(description) \
            else bleach.clean(summary)
        batch_id = structured_info['batch_id'] if 'batch_id' in structured_info else None
        try:
            embeddings= self.model.predict(np.array([self.w2v.get_sentence_matrix(data)]))
        except Exception:
            logger.error('Data is invalid.')
            return BCJStatus.NOT_FOUND, Message.UNPROCESSABLE_INPUT

        with self.__lock:
            try:
                self.database.insert(_id=structured_info['id'],
                            user_id=user_id,
                            embeddings=embeddings,
                            batch_id=batch_id)
            except DuplicateKeyError:
                return BCJStatus.BAD_REQUEST, Message.DUPLICATE_ID
   

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
        #logger.info("here")
        with self.__lock:
            try:
                self.database.delete(_id=_id,user_id=user_id)
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

        #We can't vectorize the update without a summary or a description
        if not(bool(summary) and bool(description)):
            with self.__lock:
                try:
                    if 'batch_id' in structured_info:
                        self.database.update(_id=structured_info['id'],
                                        user_id=user_id,
                                        batch_id=batch_id)
                    return BCJStatus.OK, Message.VALID_INPUT
                except (TypeError, NoUpdatesError):
                    return BCJStatus.NOT_FOUND, Message.DUPLICATE_ID
        
        #clean data and vectorize
        data = bleach.clean(description) if bool(description) \
            else bleach.clean(summary)
        try:
            embeddings= self.model.predict(np.array([self.w2v.get_sentence_matrix(data)]))
        except Exception:
            logger.error('Data is invalid.')
            return BCJStatus.NOT_FOUND, Message.UNPROCESSABLE_INPUT

        with self.__lock:
            try:
                self.database.update(_id=structured_info['id'],
                                user_id=user_id,
                                embeddings=embeddings,
                                batch_id=batch_id)
            except(TypeError, NoUpdatesError): #vantar að meðhöndla
                return BCJStatus.NOT_FOUND, Message.DUPLICATE_ID

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
                return BCJStatus.ERROR, Message.DUPLICATE_ID

        self.update_tree_for_user(user_id)

        return BCJStatus.OK, Message.VALID_INPUT

    @get_or_create_user
    def add_batch(self,user_id: int, data: list) -> Tuple[BCJStatus, Message]:
        """
        Adds a batch to the database and updates the KD-Tree

        Returns
        -------
        BCJStatus
        """
        #All batch_ids but be the same, as it is, a "batch"
        assert all(d['structured_info']['batch_id'] == data[0]['structured_info']['batch_id'] 
            for d in data)

        #Clean and prepare for vectorization
        sentences = []
        for bug in data:
            sentence = bug['description'] if bool(bug['description']) else bug['summary']
            sentences.append(bleach.clean(sentence))
        
        #vectorize sentences and combine them with the approperiate id
        embeddings = self.model.predict(np.array(self.w2v.get_sentence_matrix(sentences)))
        batch_data = [(bug['id'],user_id,embedding,bug['batch_id'])
                            for bug, embedding in zip(data, embeddings)]
        with self.__lock:
            try:
                self.database.insert_batch(batch_data)
            except (TypeError,NotFoundError, DuplicateKeyError):
                return BCJStatus.ERROR, Message.DUPLICATE_ID
        
        self.update_tree_for_user(user_id)
        return BCJStatus.OK, Message.VALID_INPUT
