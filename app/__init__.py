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
from bcj_ai import BCJAIapi as ai, BCJStatus 
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
        #Authenticate request..
        req = request.json #Retrieve JSON from GET request
        schema = Schema({ #The schematic the JSON request must follow
            'summary': str,
            'description': str,
            Optional('k'): And(int, lambda n: n>0),
            Optional('structured_info'): dict})
        try:
            schema.validate(req)
        except(SchemaError, TypeError):
            return {"message": 'JSON must at least contain the keys summary and description, both with values of type str'}, 400 
        summary = req['summary']
        description = req['description']
        if summary == "" and description == "": return {'message': 'Summary and description cannot both be empty'}, 400
        try:
            k = req['k']
        except:
            k = 5
        try:
            structured_info = req['structured_info']
        except:
            structured_info = None
        bugs = ai.get_similar_bugs_k(summary, description, k=k, structured_info=structured_info)
        return {"data": bugs[1]}, bugs[0].value
    
    def post(self):
        req = request.json
        try:
            if req['structured_info']['id'].isnumeric() and validator.validate_datestring(req['structured_info']['creationDate'][0:10]):
                result = ai.add_bug(summary=req['summary'],description=req['description'],structured_info=req['structured_info']['creationDate'])
                if result == BCJStatus.ERROR:
                    return {'message': 'Insertion failed'},result
                return  'insertion successful', result 
            else:
                return 'id(int) or date(datetime) missing or not in proper format',400
        except:
            return 'Data not in proper format, requires summary, descripion and structured_info with id and creationDate(YYY-MM-DD). Summary or description may be empty strings',400
    
    def patch(self):
        req = request.json
        
    
    def delete(self):
        #Authenticate request..
        req = request.json
        schema = Schema({
            'id': int
        })
        try:
            schema.validate(req)
        except:
            return {'message': 'JSON can only contain the key id which contains an int value'}
        result = ai.remove_bug(req['id'])
        if result == BCJStatus.OK:
            return {'message': 'Successfully removed'}, result.value
        return {'message': 'Invalid id'}, result.value

        

class Batch(Resource):
    def get(self): #Ef maður vill sækja batch sem maður senti inn?
        #Authenticate request..
        req = request.json
        schema = Schema({
            "batch_id": str
        })
        try:
            schema.validate(req)
        except(SchemaError, TypeError):
            return {'message': "JSON must only contain batch_id"}, 400
        batch = ai.get_batch_by_id()
    
    def post(self):
        #Authenticate request..
        batch_id = 0
        return batch_id
    
    def delete(self):
        #Authenticate request..
        pass


api.add_resource(Bug,'/bug')
api.add_resource(Batch, '/batch')