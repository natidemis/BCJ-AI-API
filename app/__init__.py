"""
@authors: Gitcelo, natidemis
May-June 2021

API for AI web service
"""

from flask import Flask, request, jsonify, make_response
from flask_restful import Resource, Api, reqparse
from flask_httpauth import HTTPTokenAuth
from bcj_ai import BCJAIapi as ai, BCJStatus 
from schema import Schema, And, Or, Use, Optional, SchemaError
from helper import Validator, Message
import json
import bleach
import os
import dotenv
from dotenv import load_dotenv

load_dotenv()
SECRET_TOKEN = os.getenv('SECRET_TOKEN')
app = Flask(__name__, instance_relative_config=True)
api = Api(app)
validator = Validator()
#ai = ai()
auth = HTTPTokenAuth(scheme="Bearer")

@auth.verify_token
def verify_token(token):
    if token==SECRET_TOKEN:
        return token
    
class Bug(Resource):
    """
    Web service class for working with a usability problem(UP)
    """
    @auth.login_required
    def get(self):
        """
        GET method that fetches the k UPs that are most similar to the UP
        
        Returns
        -------
        ID's of the k most similar UPs if everything went well, else an error message
        Status code
        """
        req = request.json #Retrieve JSON
        try:
            validator.validate_data(req) #Validate the JSON
        except(SchemaError, ValueError):
            return make_response(jsonify({"message": Message.FAILURE.value}), 400) #Failure message if JSON is invalid
        
        summary = bleach.clean(req['summary'])
        description = bleach.clean(req['description'])
        if summary == "" and description == "":
            return make_response(jsonify({'message': Message.UNFULFILLED_REQ.value}), 400)
        k= req['k'] if 'k' in req else 5
        structured_info = req['structured_info']
        bugs = ai.get_similar_bugs_k(summary,
                                     description,
                                     structured_info,
                                     k)
        return make_response(jsonify(data=bugs[1]),bugs[0].value)
    
    @auth.login_required
    def post(self):
        """
        Method for handling POST request on '/bug' used for inserting a UP to the AI and its database.
        
        Returns
        -------
        A message with a brief description explaining the result for the request and status code.
        """

        req = request.json
        try:
            validator.validate_data(req)
        except(SchemaError, ValueError):
            return make_response(jsonify({'message': Message.FAILURE.value}),400)
 
        if len(req['summary']) > 0 or len(req['description'])>0:
            return make_response(jsonify(data={'message': Message.VALID_INPUT.value}), ai.add_bug(
                summary=bleach.clean(req['summary']),
                description=bleach.clean(req['description']),
                structured_info=req['structured_info']).value)
        return make_response(jsonify(data={'message': Message.UNFULFILLED_REQ.value}),400)
    
    @auth.login_required
    def patch(self):
        """
        PATCH method for http request on '/bug' for updating an existing UP in the AI.

        Returns
        -------
        A message with a brief description explaining the result for the request and status code.
        """

        req = request.json
        try:
            validator.validate_update_data(req)
        except(SchemaError, ValueError):
            return make_response(jsonify(data={'message': Message.FAILURE.value}), 400)
        
        summary = bleach.clean(req['summary']) if 'summary' in req else None
        description = bleach.clean(req['description']) if 'description' in req else None
        return make_response(jsonify({'message': Message.VALID_INPUT.value}), ai.update_bug(
            summary=summary,
            description = description,
            structured_info = req['structured_info']).value)  

    @auth.login_required
    def delete(self):
        """
        Method for handling a delete request on /bug for removing an existing UP in the AI.

        Returns
        -------
        A message with a brief description of the result for the request and status code.
        """
        req = request.json
        try:
            validator.validate_id(req)
        except(SchemaError, ValueError):
            return make_response(jsonify({'message': Message.FAILURE.value}), 400)
        
        result = ai.remove_bug(req['id'])
        if result == BCJStatus.OK:
            return make_response(jsonify({'message': Message.REMOVED.value}), result.value)
        return make_response(jsonify({'message': Message.INVALID.value}), result.value)

class Batch(Resource):
    """
    Web service class for working with a batch of bugs
    """
    @auth.login_required
    def get(self):
        """
        Method for handling a get http request on /batch for fetching a batch of UPs.

        Returns
        -------
        Batch of Ups if the batch exists in the database, otherwise a message and status code
        """
        req = request.json
        try:
            validator.validate_id(req)
        except(SchemaError, ValueError):
            return make_response(jsonify({'message': Message.FAILURE.value}),400)
        
        batch = ai.get_batch_by_id(req['id'])
        return make_response(jsonify(data=batch[1]), batch[0].value)
    
    @auth.login_required
    def delete(self):
        """
        Method for handling delete request on /batch, used for deleting a batch of UPs

        Returns
        -------
        Message with a brief explanation and status code
        """
        req = request.json
        try:
            validator.validate_id(req)
        except(SchemaError, ValueError):
            return {'message': Message.FAILURE.value},400
       
        result = ai.remove_batch(req['id'])
        if result == BCJStatus.OK:
            return make_response(jsonify({'message': Message.REMOVED.value}), result.value)
        return make_response(jsonify({'message': Message.INVALID.value}), result.value)
        
api.add_resource(Bug,'/bug')
api.add_resource(Batch, '/batch')