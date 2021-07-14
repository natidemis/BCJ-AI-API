"""
Module whose sole purpose is to download stopwords from
the nltk package. Only to be used if the stopwords aren't
downloaded by default when running the server.
"""
import nltk
nltk.download('stopwords')
