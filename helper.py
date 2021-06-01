"""
Helper classes for the app
"""
from datetime import datetime
class Validator:

    def __init__(self):
        """
        A class containing validation functions for the app
        """
    def validate_datestring(self, stringdate):
        try:
            datetime.strptime(stringdate, '%Y-%m-%d')
            return True
        except:
            return False
