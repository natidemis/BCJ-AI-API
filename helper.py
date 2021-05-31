"""
Helper classes for the app
"""
import datetime
class Validator:

    def __init__(self):
        """
        A class containing validation functions for the app
        """
        def validate_datestring(self, stringdate):
            try:
                datetime.datetime.strptime(stringdate, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Incorrect date")
