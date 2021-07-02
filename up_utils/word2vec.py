# -*- coding: utf-8 -*-
"""
created on Wed Jun 19 10:14:20 2019

@author: Hugi Holm

Use gensim word2vec package based on Mikolov et al.

Use some trained model and train the model on our corpus also
"""

import string
import logging
import re
import os
import time
from glob import glob  # For any-sized glove dataset

import numpy as np
import pandas as pd
from gensim.scripts.glove2word2vec import glove2word2vec
import gensim.models
from sklearn.feature_extraction import text
import nltk
from nltk.corpus import stopwords
import up_utils.utils as utils # pylint: disable=import-error

class Word2Vec():
    """
    Static methods:
    _preprocesstext
    _preprocess

    Class methods:
    _get_wv
    _create_word2vec_wv
    _create_word2vec_wv_on_our_corpus
    get_sentence_matrix
    clear

    Instance variables:
    dataset

    Class variables:
    stop_words
    word_vector

    """

    # pylint: disable=too-few-public-methods
    # This class exists only to encode sentences (1 function)
    # and contains too much logic to be a single function.

    stop_words = None
    word_vector = None

    def __init__(
            self,
            data=None,
            wv_path='wordvectors.wv',
            dataset='commoncrawl',
            missing_word_path=None,
            **kwargs):
        """
        Initialize Word2Vec

        Arguments
        ---------
        data : str or pandas.DataFrame, optional
            Data used for training word vectors on own corpus if word vector
            file is missing. Only optional if word vector at 'wv_path' is
            present.

        wv_path : str, optional
            Path to word vector file. Defaults to 'wordvectors.wv'.

        dataset : str, optional
            Dataset to use. Options are 'commoncrawl' and 'googlenews'. Default
            is 'commoncrawl'.

        missing_word_path : str, optional
            Path to missing word log. If omitted missing words are logged to
            stdout.

        kwargs : dict, optional
            Keyword arguments used when word vector file is missing. In which
            case either 'commoncrawl_path' or 'googlenews_path' must be
            supplied.
            Keyword arguments:

                commoncrawl_path : str, optional
                    Path to commoncrawl vectors, can be a glob.

                googlenews_path : str, optional
                    Path to googlenews vectors, can be a glob.

                data : pandas.DataFrame
                    A DataFrame with bug texts to use for creating word
                    vectors.

                wv_size : int
                    Size of word vectors.
        """

        assert isinstance(data, (pd.DataFrame, str)) or data is None, \
            "'data' must either be a string or a DataFrame"
        assert dataset in ('commoncrawl', 'googlenews'), \
            "'dataset' must either be 'commoncrawl' or 'googlenews'"
        Word2Vec._missing_word_path = missing_word_path

        if isinstance(data, str):
            logging.info("Loading data data from file %s",
                         data)
            data = pd.read_csv(
                data,
                index_col=0,
                sep='|',
                )

        if data is None:
            # Make an empty dataframe to pass on
            logging.info("No dataframe given - creating empty dataframe")
            col_names = ['summary', 'description']
            data = pd.DataFrame(columns=col_names)
            logging.info("Empty dataframe created")

        self.dataset = dataset

        if Word2Vec.stop_words is None:
            my_stop_words = [
                '!', '$', '\'', '(', ')', '-', '.', 'ha', 'le', 'u', 'wa',
                '\'\'', '/', '...', '[', ']', '\'s', ',', ':', '``', ';', '&',
                '#', '?', '<', '>', '“', '”', '|',
            ]

            # Stop words may not be present
            try:
                logging.info("Importing stopwords.")
                print("Importing stop words")
                Word2Vec.stop_words = stopwords.words("english")
            except ValueError:
                logging.info("No nltk stopwords present. Downloading now.")
                nltk.download('stopwords')
                Word2Vec.stop_words = stopwords.words("english")

            my_stop_words = Word2Vec.stop_words + my_stop_words
            Word2Vec.stop_words = text.ENGLISH_STOP_WORDS.union(my_stop_words)

        # Set word vector as a singleton
        if Word2Vec.word_vector is None:
            print("Initializing word2vec word vector...")
            Word2Vec.word_vector = self._get_wv(wv_path, data=data, **kwargs)

    def _get_wv(self, wv_path, wv_size=300, **kwargs):
        """
        get_wv

        Arguments
        ---------
        wv_path : str
            Path to word vector file.

        kwargs : dict, optional
            Keyword arguments passed to '_create_word2vec_wv' and
            '_create_word2vec_wv_on_our_corpus'.
        """

        logging.info(
            "Loading wordvectors trained on our corpus, "
            "i.e. the words not in %s...",
            self.dataset,
            )
        try:
            # if there is a keyed vector just load it in,
            # instead of creating a new one.
            logging.info("Attempting to load an already available keyed "
                         "vector.")
            word2vec_wv = gensim.models.KeyedVectors.load(wv_path)
            logging.info("Loading successful.")
            print("Successfully fetched word vectors from file")
        except FileNotFoundError:
            logging.info("No keyed vector available:")
            logging.info(
                "Creating the word2vec word vectors with %s",
                self.dataset,
                )
            # word vectors
            word2vec_wv = self._create_word2vec_wv(**kwargs)
            logging.info("Training word vectors on our corpus.")
            word2vec_wv = Word2Vec._create_word2vec_wv_on_our_corpus(wv_size=wv_size, **kwargs)
            logging.info("Traing complete. Saving the trained wordvectors.")
            word2vec_wv.save(wv_path)
            print("Successfully created word vectors, with data from our "
                  "corpus")
        logging.info("Word2vec created")
        return word2vec_wv

    # create the word vector
    def _create_word2vec_wv(
            self,
            commoncrawl_path=None,
            googlenews_path=None,
            **kwargs): # pylint: disable=unused-argument
        """
        Description:
        Create word2vec word vectors from a pretrained dataset
        """

        assert commoncrawl_path is not None or googlenews_path is not None, \
            "At least one of 'commoncrawl' and 'googlenews' must be supplied"

        # It is not possible to train this loaded keyedvector on our personal
        # sentences
        # https://stackoverflow.com/questions/42626287/gensim-keyedvectors-train
        # they use word2vec trained on google news

        print("Loading pre-trained word vectors from file (this can take up "
              "to an hour on the first run)")
        if self.dataset == "commoncrawl":  # use glove vectors (common crawl)
            filepath = glob(commoncrawl_path)[0]
            outputfile = "Model/gensim_glove_vectors.txt"
            try:
                logging.info("Attempting to load word2vec from file")
                word2vec_wv = gensim.models.KeyedVectors.load_word2vec_format(
                    outputfile,
                    binary=False,
                    )
            except FileNotFoundError:
                logging.info("Loading failed. Converting GloVe to Word2Vec...")
                glove2word2vec(
                    glove_input_file=filepath,
                    word2vec_output_file=outputfile,
                    )
                logging.info("Conversion complete.")
                logging.info("Loading Word2Vec keyed vector...")
                word2vec_wv = gensim.models.KeyedVectors.load_word2vec_format(
                    outputfile,
                    binary=False,
                    )

        else:
            logging.info("Loading Google News keyed vector...")
            word2vec_wv = gensim.models.KeyedVectors.load_word2vec_format(
                glob(googlenews_path)[0],
                binary=True,
                )

        logging.info("Loading vector complete.")
        Word2Vec.word_vector = word2vec_wv
        return Word2Vec.word_vector

    @classmethod
    def _create_word2vec_wv_on_our_corpus(
            cls,
            data,
            wv_size,
            **kwargs): # pylint: disable=unused-argument
        """
        Arguments
        ---------

        data : pandas.DataFrame
            A DataFrame with bugs to use for training Word2Vec on our data

        wv_size : int
            Size of word vectors

        kwargs : Key-word arguments
            Unused
        """

        # prepare all the data sentences for the model, preprocess
        print("Creating word vectors with our corpus")
        logging.info("Preprocessing text for creating word vectors on our "
                     "corpus")

        sentences = []
        for index in data.index:
            assert isinstance(index, (int, float))

            description_types = set(["description",
                                     "summary",
                                     "Problems"])

            # Remove descripton types not present
            for description_type in description_types.copy():
                if description_type not in data:
                    description_types.remove(description_type)

            for description_type in description_types:
                sentence = data.loc[index, description_type]
                sentence = Word2Vec._preprocess(sentence)
                sentences.append(sentence)

        logging.info("Preprocessing complete")

        # create a new model to train on our corpus
        # then add the trained words to our keyed vector word2vec_wv
        model = gensim.models.Word2Vec(
            min_count=1,
            vector_size=wv_size,
            workers=os.cpu_count(),
            )
        model.build_vocab(sentences)

        if len(sentences) > 0:
            logging.info("Training Word2Vec on our sentences...")
            model.train(
                sentences,
                total_examples=len(sentences),
                epochs=5, # This might not be enough
                )
            logging.info("Done training Word2Vec.")

        time_point = time.time()
        # Try using sets
        missing_keys = list(
            set(model.wv.key_to_index.keys())
            -
            set(cls.word_vector.key_to_index.keys())
            )

        weights = []
        for entity in missing_keys:
            weights.append(model.wv[entity])
        logging.debug(
            "Time to create `weights` and `missing_keys`: %.3f",
            time.time()-time_point
            )

        # Batch add vectors
        assert len(missing_keys) == len(weights)
        if len(missing_keys) > 0:
            time_point = time.time()
            cls.word_vector.add_vectors(
                missing_keys,
                weights,
                )
            logging.debug(
                "Time to add weights to word vector: %.3f",
                time.time()-time_point,
                )
        else:
            logging.debug("No weghts added to word vector")

        if __debug__:
            time_point = time.time()
            wv_keys = set(cls.word_vector.key_to_index.keys())
            assert len(set(missing_keys) - wv_keys) == 0
            logging.info(
                "Time to verify that words are present: %.3f",
                time.time()-time_point,
                )

        return cls.word_vector

    @classmethod
    def get_sentence_matrix(
            cls,
            sentence,
            seq_len=100,
            word_vector_size=300):
        """
        Arguments:
        sentence -- a sentence, the text from the bug report
        Returns:
        A sequence of Word2Vec vectors (a matrix) representing `sentence`,
        of shape (seq_len, wv_len) — wv_len is 300 for gensim.Word2Vec
        """

        assert cls.word_vector is not None
        word2vec_wv = cls.word_vector

        # number of words not in corpus
        output = []

        if utils.not_nan(sentence):
            for word in Word2Vec._preprocess(
                    sentence):

                word_vector = None
                try:
                    word_vector = word2vec_wv[word]
                except KeyError:
                    # Use 0-vector if word is missing
                    cls.log_missing_word(word)
                    word_vector = [0]*word_vector_size

                output.append(word_vector)
                if len(output) == seq_len:
                    break

        # Prepend 0-vectors to sentence matrix such that
        # sentence matrix has the same amount of timesteps
        if seq_len is not None:
            for _ in range(seq_len-len(output)):
                output.insert(
                    0,
                    np.zeros(
                        word_vector_size,
                        dtype=np.float32,
                        ),
                    )
        return np.array(output)

    @classmethod
    def _log_missing_word_init(cls, word):
        if cls._missing_word_path is None:
            cls._missing_word_file = None
        else:
            # pylint: disable=consider-using-with
            cls._missing_word_file = open(cls._missing_word_path,
                                          'a', encoding='utf-8')
        cls.log_missing_word = cls._log_missing_word
        cls.log_missing_word(word)

    @classmethod
    def _log_missing_word(cls, word):
        print(f"Word {word} not found", file=cls._missing_word_file)

    @classmethod
    def log_missing_word(cls, word):
        """ Log word which is missing from Word2Vec vocabulary """
        cls._log_missing_word_init(word)

    @classmethod
    def clear(cls):
        """
        Remove class data, freeing up memory

        WARNING:
        This will cause crashes in other Word2Vec instances,
        so make sure there is only one!
        """

        cls.word_vector = None
        cls.stop_words = None
        if cls._missing_word_file is None:
            cls._missing_word_file.close()
        cls.log_missing_word = cls._log_missing_word_init

    @staticmethod
    def _preprocess(doc):
        """
        Description:
        Preprocess a document

        Arguments:
        doc -- Document to preprocess
        """

        sentence = [
            t
            for t in Word2Vec._preprocesstext(doc).split()
            if t not in Word2Vec.stop_words and len(t) > 1
            ]
        return sentence

    @staticmethod
    def _preprocesstext(doc):
        """
        Preprocess a text

        Arguments:
        doc -- Document to preprocess
        """

        if utils.is_nan(doc):
            return ""
        assert isinstance(doc, str), f"Doc must be a string! Doc: {doc}"

        try:
            lowercase = doc.lower()
            strpunct = string.punctuation + "“”"
            nopunct = lowercase.translate(
                str.maketrans(
                    strpunct,
                    " "*len(strpunct),
                    ),
                )
            nonum = re.sub(
                r"\d+",
                " ",
                nopunct,
                )
        except (ValueError, AttributeError):
            if str(doc) != 'nan':
                logging.debug("Doc: %s", doc)

            nonum = ""

        return nonum
