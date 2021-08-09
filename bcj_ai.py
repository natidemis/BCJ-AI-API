# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=W0703
# pylint: disable=W0613
# pylint: disable=W0212
"""
@authors: kra33, Gitcelo, natidemis
May 2021

API module for Bug Consolidation for Jira (BCJ) AI model.
Used to store bugs and classify them.
"""

from __future__ import annotations
from enum import IntEnum, Enum
import os
from threading import Lock
from typing import Tuple, Union
import tensorflow as tf
import numpy as np
import bleach
from dotenv import load_dotenv
from up_utils.word2vec import Word2Vec
from up_utils.kdtree import KDTreeUP as KDTree
from Misc.db import Database, NotFoundError,DuplicateKeyError, NoUpdatesError
from Misc.log import logger

load_dotenv()

def authenticate_user(fn):
    """
    Decorator function for validating the given user_id.
    If the user exists, fetch data for that 'user'.

    Arguments
    ---------
    None

    Returns
    -------
    Decorator to be applied to a function.
    """
    async def decorator(self, *args, **kwargs):
        user_id = kwargs.get('user_id')
        if user_id in self.users:
            if self.current_user != user_id:
                await self._update_tree_for_user(user_id)
        else:
            logger.error('User: %s not in database: %s, Auth failed',user_id,self.users)
            raise ValueError('User not available')
        return await fn(self, *args, **kwargs)
    return decorator

def get_or_create_user(fn):
    """
    Decorator function for validating the given user_id.
    If the user exists, fetch data for that 'user'.
    Otherwise, create a new user for the given user_id
    Returns

    Arguments
    --------
    None

    -------
    Decorator to be applied to a function.
    """
    async def decorator(self, *args, **kwargs):
        user_id = kwargs.get('user_id')
        if user_id in self.users:
            if self.current_user != user_id:
                await self._update_tree_for_user(user_id)
        else:
            try:
                with self._lock:
                    await self._database.insert_user(user_id)
                self.users.add(user_id)
                await self._update_tree_for_user(user_id)
            except (TypeError, DuplicateKeyError) as e:
                logger.error('Inserting user: %s failed for err: %s',user_id, e)
                raise ValueError from e
        return await fn(self, *args, **kwargs)
    return decorator

class BCJMessage(Enum):
    """
    BCJAIapi response messages
    """
    UNPROCESSABLE_INPUT = 'Something is wrong with the inserted data.'
    VALID_INPUT = 'Valid input, check status for result'
    FAILURE = ('''Data not in proper format, read the requirement on github:
    https://github.com/natidemis/BCJ-AI-API''')
    UNFULFILLED_REQ = 'Either summary or description must have length > 0'
    UNAUTHORIZED = 'Unauthorized, wrong token'
    REMOVED = 'Successfully removed'
    DUPLICATE_ID = "This Id already exists for the given user"
    DUPLICATE_ID_BATCH = "One of the given bug Id's already exists for this user"
    NO_EXAMPLE = 'There is no example with the the given ID for this user.'
    INVALID_ID_OR_DATE = ("Either the id already exists or "
                "the given date is not valid")
    NO_USER = "User not available."
    NO_UPDATES = "There were no updates to make."
    NO_DELETION = "There was nothing to delete for the given (user_id, id) pair."
    EMPTY_TREE = "No examples available"

class BCJStatus(IntEnum):
    """
    Class that contains status codes
    """
    OK = 200
    NOT_FOUND = 404
    ERROR = 500
    BAD_REQUEST = 400
    NOT_IMPLEMENTED = 501

class BCJAIapi:
    """
    API class for AI

    Class methods:
    initialize


    Instance variables:
        users:
            All users currently available in the database
        current_user:
            current user of the instance
        kdtree: up_utils.kdtree
            nearest neighbour look up

    Instance methods:
        get_similar_bugs_k
        add_bug
        remove_bug
        update_bug
        remove_batch
        add_batch
    """

    _w2v = Word2Vec(
            outputfile=os.getenv('OUTPUT_FILE'),
            dataset=os.getenv('DATASET'), # Dataset can either be googlenews or commoncrawl,
            commoncrawl_path=os.getenv('COMMONCRAWL_PATH'),
            googlenews_path=os.getenv('GOOGLENEWS_PATH'))   

    _model = tf.keras.models.load_model('Models', compile=False)

    def __init__(self, users: set, database: Database):
        """
        Initialize the AI model from disk; read embedding vectors from disk;
        get ready for classifying bugs and returning similar bug ids.

        Requirements:
            Initialized using the classmethod 'initialize'.

        Arguments
        ---------
        users - set:
            A set of user_ids currently available
        database - db.Database
            a database object with a connection pool.

        Returns
        -------
        BCJAIapi object.
        """

        self._lock = Lock()
        self._database = database
        self.users = users
        self.kdtree = None
        self.current_user = int()


    @classmethod
    async def initalize(cls, database: Database) -> BCJAIapi:
        """
        Initialize a BCJAIapi object with a given database object.
        Initializes 'users' for all users currently available from the database.

        Arguments
        ---------
        database - db.Database:
            Database object with a connection pool

        Returns
        -------
        BCJAIapi object initialized with all available users.
        """
        try:
            users = set(await database.fetch_users())
        except NotFoundError:
            users = set()
        logger.info('Initialized BCJAIapi with users: %s', users)
        return cls(users,database)

    def _restructure_tree(self,new_data: list) -> KDTree:
        """
        Private method for updating 'kdtree'.

        Arguments
        ---------
            new_data: list[dict]
                data containing a list of embeddings and IDs

        Returns
        -------
        None, constructs self.kdtree with a new KDTree object as necessary.
        """
        if new_data:
            embeddings = np.vstack([data['embeddings'] for data in new_data])
            ids = np.array([data['id'] for data in new_data])
            self.kdtree=KDTree(data=embeddings, indices=ids)
        else:
            self.kdtree = None


    async def _update_tree_for_user(self, user_id: str) -> None:
        """
        Update 'self.kdtree' approperiately for `user_id`

        Arguments
        ---------
        user_id: int

        Returns
        -------
        None
        """
        with self._lock:
            try:
                data = await self._database.fetch_all(user_id)
                self._restructure_tree(data)
            except NotFoundError:
                self.kdtree = None
            finally:
                self.current_user = user_id


    @authenticate_user
    async def get_similar_bugs_k(self,#pylint: disable=too-many-arguments
                            user_id: str,
                            summary: str = "",
                            description: str = "",
                            structured_info: str=None,
                            k: int=5) -> Tuple[BCJStatus, Union[dict,str]]:
        """
        Return the IDs and distances(percentage) of the k most similar bugs
        based on given summary, desription, and structured information.

        Arguments
        ---------
            user_id: str
                Indentification number of the user: must exist in the database
            summary: str
                A brief summary of the bug
            description: str
                A description of the bug
            structured info: dict {'id': int, 'date': str, 'batch_id': int | None}
                'date': str
                    A string representation of a date for the bug

            'k': int
                The number of similar bugs to fetch

        Returns
        -------
        BCJStatus, dict containing Id's and distances of the 'k' most similar
        """

        assert bool(summary) or bool(description)

        #prepare data for vectorization and insertion
        data = bleach.clean(description) if bool(description) \
            else bleach.clean(summary)
        if self.kdtree is None:
            logger.info('KDTree is empty for user: %s', user_id)
            raise NotFoundError

        N = len(self.kdtree.indices)
        k = min(k,N)

        try:
            vec= BCJAIapi._model.predict(np.array([BCJAIapi._w2v.get_sentence_matrix(data)]))
        except Exception:
            logger.error('Could not predict/vectorize for %s', data)
            return BCJStatus.NOT_IMPLEMENTED, BCJMessage.UNPROCESSABLE_INPUT

        with self. _lock:
            dists,ids = self.kdtree.query(vec, k=k)

        response = {
            "id": ids.flatten().tolist(),
            "dist": dists.flatten().tolist()
        }

        return BCJStatus.OK, response

    @get_or_create_user
    async def add_bug(self,
                user_id: str,
                structured_info: dict,
                summary: str="",
                description: str="") -> Tuple[BCJStatus, BCJMessage]:
        """
        Add a bug with given summary, description and structured information.

        Arguments
        ---------
            user_id: str
                Indentification number of the user: must exist in the database
            summary: str
                A brief summary of the bug
            description: str
                A description of the bug
            structured info: dict {'id': int, 'date': str, 'batch_id': int | None}
                'id': int
                    Id for the bug
                'date': str
                    A string representation of a date for the bug
                'batch_id: int | None
                    the Id which this bug belongs to, None other if no such Id exists

        Returns
        -------
        BCJStatus, BCJMessage

        """
        assert bool(description) or bool(summary)
        # Sanitize and prepare the data for vectorization and insertion
        data = bleach.clean(description) if bool(description) \
            else bleach.clean(summary)
        batch_id = structured_info['batch_id'] if 'batch_id' in structured_info else None
        try:
            embeddings= BCJAIapi._model.predict(np.array([BCJAIapi._w2v.get_sentence_matrix(data)]))
        except Exception:
            logger.error('Data is invalid for %s',data)
            return BCJStatus.NOT_IMPLEMENTED, BCJMessage.UNPROCESSABLE_INPUT

        with self._lock:
            try:
                await self._database.insert(id=structured_info['id'],
                            user_id=user_id,
                            embeddings=embeddings,
                            batch_id=batch_id)
            except DuplicateKeyError:
                return BCJStatus.BAD_REQUEST, BCJMessage.DUPLICATE_ID


        with self._lock:
            if self.kdtree is None:
                self.kdtree = KDTree(data=embeddings, indices=[structured_info['id']])
            else:
                self.kdtree.update(embeddings, structured_info['id'])

        return BCJStatus.OK, BCJMessage.VALID_INPUT

    @authenticate_user
    async def remove_bug(self,user_id: str, id: int) -> Tuple[BCJStatus, BCJMessage]: #pylint: disable=redefined-builtin
        """
        Remove a bug with 'id' for the given 'user_id'

        Arguments
        ---------
            user_id: str
                Indentification number of the user: must exist in the database
            id: int
                Id for the bug

        Returns
        -------
        BCJstatus, BCJMessage
        """

        with self._lock:
            try:
                await self._database.delete(id=id,user_id=user_id)
            except NoUpdatesError:
                return BCJStatus.NOT_FOUND, BCJMessage.NO_EXAMPLE
        await self._update_tree_for_user(user_id)
        return BCJStatus.OK, BCJMessage.VALID_INPUT

    @authenticate_user
    async def update_bug(self,
                    user_id: str,
                    structured_info: dict,
                    summary: str="",
                    description: str="") -> Tuple[BCJStatus, BCJMessage]:
        """
        Updates a bug with the parameters given. The id of the bug should be in structured_info.

        Arguments
        ---------
            user_id: str
                Indentification number of the user: must exist in the database
            summary: str
                A brief summary of the bug
            description: str
                A description of the bug
            structured info: dict {'id': int, 'date': str, 'batch_id': int | None}
                'id': int
                    Id for the bug
                'date': str
                    A string representation of a date for the bug
                'batch_id: int | None
                    the Id which this bug belongs to, None other if no such Id exists

        Returns
        -------
        BCJStatus, BCJMessage
        """

        batch_id = structured_info['batch_id'] if \
                        'batch_id' in structured_info else None

        #We can't vectorize the update without a summary or a description
        if not bool(summary) and not bool(description):
            if 'batch_id' not in structured_info:
                return BCJStatus.BAD_REQUEST, BCJMessage.NO_UPDATES
            with self._lock:
                try:
                    if 'batch_id' in structured_info:
                        await self._database.update(id=structured_info['id'],
                                        user_id=user_id,
                                        batch_id=batch_id)
                        return BCJStatus.OK, BCJMessage.VALID_INPUT
                except NoUpdatesError:
                    return BCJStatus.BAD_REQUEST, BCJMessage.NO_UPDATES

        #clean data and vectorize
        data = bleach.clean(description) if bool(description) \
            else bleach.clean(summary)
        try:
            embeddings= BCJAIapi._model.predict(np.array([BCJAIapi._w2v.get_sentence_matrix(data)]))
        except Exception:
            logger.error('Data is invalid for %s',data)
            return BCJStatus.NOT_IMPLEMENTED, BCJMessage.UNPROCESSABLE_INPUT

        with self._lock:
            try:
                await self._database.update(id=structured_info['id'],
                                user_id=user_id,
                                embeddings=embeddings,
                                batch_id=batch_id)
            except(TypeError, NoUpdatesError):
                return BCJStatus.BAD_REQUEST, BCJMessage.NO_UPDATES

        await self._update_tree_for_user(user_id)

        return BCJStatus.OK, BCJMessage.VALID_INPUT

    @authenticate_user
    async def remove_batch(self,user_id: str, batch_id: int) -> Tuple[BCJStatus, BCJMessage]:
        """
        Removes a batch of bugs. The batch's id is idx.

        Arguments
        ---------
            user_id: str
                Indentification number of the user: must exist in the database
            batch_id: int
                Identification number of the batch

        Returns
        -------
        BCJStatus, BCJMessage
        """
        with self._lock:
            try:
                await self._database.delete_batch(batch_id,user_id)
            except NoUpdatesError:
                return BCJStatus.BAD_REQUEST, BCJMessage.NO_DELETION

        await self._update_tree_for_user(user_id)

        return BCJStatus.OK, BCJMessage.VALID_INPUT

    @get_or_create_user
    async def add_batch(self,user_id: str, data: list) -> Tuple[BCJStatus, BCJMessage]:
        """
        Adds a batch to the database and updates the KD-Tree

        Arguments
        ---------
            user_id: str
                Indentification number of the user: must exist in the database
            data: list[dict]
                summary: str
                    A brief summary of the bug
                description: str
                    A description of the bug
                structured info: dict {'id': int, 'date': str, 'batch_id': int | None}
                    'id': int
                        Id for the bug
                    'date': str
                        A string representation of a date for the bug
                    'batch_id: int | None
                        the Id which this bug belongs to, None other if no such Id exists

        Returns
        -------
        BCJStatus, BCJMessage
        """
        #All batch_ids but be the same, as it is, a "batch"
        assert all(d['structured_info']['batch_id'] == data[0]['structured_info']['batch_id']
            for d in data)

        #Clean and prepare for vectorization
        sentences = []
        for bug in data:
            sentence = bug['description'] if bool(bug['description']) else bug['summary']
            if not bool(sentence):
                raise AssertionError
            sentences.append(bleach.clean(sentence))

        #vectorize sentences and combine them with the approperiate id
        try:
            embeddings = BCJAIapi._model.predict(np.array(BCJAIapi._w2v.get_sentence_matrix(sentences)))
        except Exception:
            logger.error('Data is invalid: %s', sentences)
            return BCJStatus.NOT_IMPLEMENTED, BCJMessage.UNPROCESSABLE_INPUT
        batch_data = [(bug['structured_info']['id'],user_id,
                            embedding,bug['structured_info']['batch_id'])
                            for bug, embedding in zip(data, embeddings)]
        with self._lock:
            try:
                await self._database.insert_batch(batch_data)
            except DuplicateKeyError:
                return BCJStatus.ERROR, BCJMessage.DUPLICATE_ID_BATCH

        await self._update_tree_for_user(user_id)
        return BCJStatus.OK, BCJMessage.VALID_INPUT
