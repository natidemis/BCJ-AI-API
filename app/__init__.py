"""
@authors: Marcelo Audibert, Natanel Demissew
May 2021

API for AI web service
"""

"""
TODO:

Authentication, sanitization, valdiation
"""

from flask import Flask, request
from flask_restful import Resource, Api, reqparse
import pandas as pandas
import ast
import datetime
from bcj_ai import BCJAIapi as ai
from helper import Validator

app = Flask(__name__, instance_relative_config=True)
api = Api(app)
app.config.from_object('config')

ai = ai()
class Bug(Resource):
    def get(self):
        req = request.json #Retrieve JSON from GET request
        try:
            summary = req['summary']
            description = req['description']
            k = req['k']
        except:
            raise Exception('The JSON must contain the following keys: summary, description, and k')
        if summary == "" and description == "": return 'Summary and description cannot both be empty'
        bugs = ai.get_similar_bugs_k(summary, description, k=k)
        return bugs[1],bugs[0].value
    
    def post(self):
        req = request.json
        try:
            if 'id' in req['structured_info'] and 'creationDate' in req['structured_info']:
                try:
                    if req['structured_info']['id'].isnumeric():
                        date = req['structured_info']['creationDate']
                        date = date[0:date.find('T')]
                        Validator.validate_datestring(date)
                        print(date)
                        structured_info = {
                            'id': req['structured_info']['id'],
                            'creationDate': date
                        }
                        return {'message': ''}, ai.add_bug(summary=req['summary'],description=req['description'],structured_info=structured_info)
                except:
                    return {'message': 'id or creationDate not in correct format'},400
            else:
                return {'message': 'structured info requires both id and creation date'},400
        except:
            return {'message': 'Data not in proper format'}, 400
    
    def patch(self):
        req = request.json
        
    
    def delete(self):
        pass


class BugBatch(Resource):
    def get(self): #Ef maður vill sækja batch sem maður senti inn?
        pass
    
    def post(self):
        pass
    
    def delete(self):
        pass


api.add_resource(Bug,'/bug')
api.add_resource(BugBatch, '/bug-batch')