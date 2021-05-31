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
from bcj_ai import BCJAIapi as ai

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
        pass
    
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