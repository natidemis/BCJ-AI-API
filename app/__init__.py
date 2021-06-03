"""
@authors: Gitcelo, natidemis
May-June 2021

API for AI web service
"""

from flask import Flask, request, jsonify, make_response
from flask_restful import Resource, Api, reqparse
from bcj_ai import BCJAIapi as ai, BCJStatus 
from schema import Schema, And, Or, Use, Optional, SchemaError
import dateutil.parser
from helper import Helper, Message
import json
import bleach

app = Flask(__name__, instance_relative_config=True)
api = Api(app)
app.config.from_object('config')
helper = Helper()
ai = ai()    

class Bug(Resource):
    """
    Web service class for working with one bug
    """
    
    def get(self):
        """
        GET class that fetches the k bugs that are most similar to the one bug.
        
        Returns
        -------
        ID's of the k most similar bugs if everything went well, else an error message
        Status code
        """
        req = request.json #Retrieve JSON
        try:
            helper.validate_data(req) #Validate the JSON
        except(SchemaError, ValueError):
            return make_response(jsonify({"message": Message.FAILURE.value}), 400) #Failure message if JSON is invalid
        if not helper.auth_token(req['token']):
            return make_response(jsonify({'message': Message.UNAUTHORIZED.value}),401) #Message if wrong token
        summary = bleach.clean(req['summary'])
        description = bleach.clean(req['description'])
        if summary == "" and description == "":
            return make_response(jsonify({'message': Message.UNFULFILLED_REQ.value}), 400)
        k= req['k'] if 'k' in req else 5
        structured_info = req['structured_info']
        bugs = ai.get_similar_bugs_k(summary,
                                     description,
                                     k,
                                     structured_info)
        return make_response(jsonify(data=bugs[1]),bugs[0].value)
    
    def post(self):
        req = request.json
        try:
            helper.validate_data(req)
        except(SchemaError, ValueError):
            return make_response(jsonify({'message': Message.FAILURE.value}),400)
        if not helper.auth_token(req['token']):
            return make_response(jsonify({'message': Message.UNAUTHORIZED.value}),401)
        if len(req['summary']) > 0 or len(req['description'])>0:
            return make_response(jsonify(data={'message': Message.VALID_INPUT.value}), ai.add_bug(
                summary=bleach.clean(req['summary']),
                description=bleach.clean(req['description']),
                structured_info=req['structured_info']).value)
        return make_response(jsonify(data={'message': Message.UNFULFILLED_REQ.value}),400)
    
    def patch(self):
        req = request.json
        try:
            helper.validate_data(req)
        except(SchemaError, ValueError):
            return make_response(jsonify(data={'message': Message.FAILURE.value}), 400)
        if not helper.auth_token(req['token']):
            return make_response(jsonify({'message': Message.UNAUTHORIZED.value}),401)
        return make_response(jsonify({'message': Message.VALID_INPUT.value}), ai.update_bug(
            idx=req['structured_info']['id'],
            summary=bleach.clean(req['summary']),
            description = bleach.clean(req['description']),
            structured_info = req['structured_info']).value)      
        
    def delete(self):
        req = request.json
        try:
            helper.validate_id(req)
        except(SchemaError, ValueError):
            return make_response(jsonify({'message': Message.Failure.value}), 400)
        if not helper.auth_token(req['token']):
            return make_response(jsonify({'message': Message.UNAUTHORIZED.value}),401)
        result = ai.remove_bug(req['id'])
        if result == BCJStatus.OK:
            return make_response(jsonify({'message': Message.REMOVED.value}), result.value)
        return make_response(jsonify({'message': Message.INVALID.value}), result.value)

class Batch(Resource):
    """
    Web service class for working with a batch of bugs
    """
    
    def get(self):
        req = request.json
        try:
            helper.validate_id(req)
        except(SchemaError, ValueError):
            return make_response(jsonify({'message': Message.FAILURE.value}),400)
        if not helper.auth_token(req['token']):
            return make_response(jsonify({'message': Message.UNAUTHORIZED.value}),401)
        batch = ai.get_batch_by_id(req['id'])
        return make_response(jsonify(data=batch[1]), batch[0].value)

    def delete(self):
        req = request.json
        try:
            helper.validate_id(req)
        except(SchemaError, ValueError):
            return {'message': Message.FAILURE.value},400
        if not helper.auth_token(req['token']):
            return make_response(jsonify({'message': Message.UNAUTHORIZED.value}),401)
        result = ai.remove_batch(req['id'])
        if result == BCJStatus.OK:
            return make_response(jsonify({'message': Message.REMOVED.value}), result.value)
        return make_response(jsonify({'message': Message.INVALID.value}), result.value)
        
api.add_resource(Bug,'/bug')
api.add_resource(Batch, '/batch')