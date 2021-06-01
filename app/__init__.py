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
from bcj_ai import BCJStatus 
from helper import Validator
from schema import Schema, And, Use, Optional, SchemaError
import dateutil.parser

app = Flask(__name__, instance_relative_config=True)
api = Api(app)
app.config.from_object('config')
validator = Validator()
ai = ai()
class Bug(Resource):
    def get(self):
        req = request.json #Retrieve JSON from GET request
        schema = Schema({
            'summary': str,
            'description': str,
            'k': And(int, lambda n: n>0)})
        try:
            schema.validate(req)
        except(SchemaError):
            raise SchemaError('JSON must contain the keys summary, description, and k with values str, str, and int greater than 0, respectively')
        except(TypeError):
            return 'bl'
        summary = req['summary']
        description = req['description']
        if summary == "" and description == "": raise Exception('Summary and description cannot both be empty')
        k = req['k']
        bugs = ai.get_similar_bugs_k(summary, description, k=k)
        return bugs[1],bugs[0].value
    
    def post(self):
        req = request.json
        try:
            if req['structured_info']['id'].isnumeric() and validator.validate_datestring(req['structured_info']['creationDate'][0:10]):
                result = ai.add_bug(summary=req['summary'],description=req['description'],structured_info=req['structured_info']['creationDate'])
                if result == BCJStatus.ERROR:
                    return {'message': 'Insertion failed'},result
                return {'message': 'insertion successful'}, result 
            else:
                return {'message': 'id(int) or date(datetime) missing or not in proper format'},400
        except:
            return {'message': 'Data not in proper format, requires summary, descripion and structured_info with id and creationDate(YYY-MM-DD). Summary or description may be empty strings'},400
    
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