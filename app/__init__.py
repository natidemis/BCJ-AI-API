"""
@authors: Marcelo Audibert, Natanel Demissew
May 2021

API for AI web service
"""

"""
TODO:

Authentication, sanitization, valdiation
"""

from flask import Flask, request, jsonify, make_response
from flask_restful import Resource, Api, reqparse
import pandas as pandas
import ast
from bcj_ai import BCJAIapi as ai, BCJStatus 
from schema import Schema, And, Use, Optional, SchemaError,Or
import dateutil.parser
from helper import Helper,Message
import json

app = Flask(__name__, instance_relative_config=True)
api = Api(app)
app.config.from_object('config')
helper = Helper()
ai = ai()
class Bug(Resource):
    def get(self):
        #Authenticate request..
        req = request.json #Retrieve JSON from GET request
        schema = Schema({ #The schematic the JSON request must follow
            'summary': str,
            'description': str,
            Optional('k'): And(int, lambda n: n>0),
            'structured_info': dict})
        try:
            schema.validate(req)
        except(SchemaError, TypeError):
            return {"message": 'JSON must at least contain the keys summary, description, and structured info of types str, str, and dict respectfully'}, 400 
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
        return make_response(jsonify(data=bugs[1]),bugs[0].value)
    
    def post(self):
        req = request.json
        try:
            helper.validate_data(req)
            if len(req['summary']) > 0 or len(req['description'])>0:
                return make_response(jsonify(data={'message': Message.VALID_INPUT.value}), ai.add_bug(
                   summary=req['summary'],
                   description=req['description'],
                   structured_info=req['structured_info']
               ).value)
            else:
                return make_response(jsonify(data={'message': Message.UNFULFILLED_REQ.value}),400)
        except:
            return make_response(jsonify(data={'message': Message.FAILURE.value}),400)
    
    def patch(self):
        req = request.json
        try:
            helper.validate_data(req)
            return {'message': Message.VALID_INPUT.value}, ai.update_bug(
                idx=req['structured_info']['id'],
                summary=req['summary'],
                description = req['description'],
                structured_info = req['structured_info']
                ).value
        except:
            return make_response(jsonify(data={'message': Message.FAILURE.value}), 400)
        

    
    def delete(self):
        #Authenticate request..
        req = request.json
        schema = Schema({
            'id': int
        })
        try:
            schema.validate(req)
        except:
            return {'message': 'JSON can only contain id'}
        result = ai.remove_bug(req['id'])
        if result == BCJStatus.OK:
            return {'message': 'Successfully removed'}, result.value
        return {'message': 'Invalid id'}, result.value

        

class Batch(Resource):
    def get(self): #Ef maður vill sækja batch sem maður senti inn?
        #Authenticate request..
        req = request.json
        schema = Schema({
            "batch_id": int
        })
        try:
            schema.validate(req)
        except(SchemaError, TypeError):
            return {'message': "JSON must only contain batch_id"}, 400
        batch = ai.get_batch_by_id(req['batch_id'])
        return make_response(jsonify(data=batch[1]), batch[0].value)
    
    def post(self):
        #Authenticate request..
        #data = request.json
        #for req in data:
        #    try:
        #        helper.validate_data(req)
        #        if len(req['summary']) > 0 or len(req['description'])>0:
        #            return {'message': Message.SUCCESS.value}, 
        #        else:
        #            return {'message': Message.UNFILLED_REQ.value},400
        #    except:
        #        return {'message': Message.FAILURE.value},400
        #
        pass

    def delete(self):
        #Authenticate request..
        req = request.json
        schema = Schema({
            "batch_id": int
        })
        try:
            schema.validate(req)
        except(SchemaError, TypeError):
            return {'message': "JSON must only contain batch_id"}, 400
        result = ai.remove_batch(req['batch_id'])
        if result == BCJStatus.OK:
            return {'message': 'Successfully removed'}, result.value
        return {'message': 'Invalid id'}, result.value
        


api.add_resource(Bug,'/bug')
api.add_resource(Batch, '/batch')