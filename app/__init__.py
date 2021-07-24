# pylint: disable=R0201
"""
@authors: Gitcelo, natidemis
May-June 2021

API for AI web service
"""

import json
import os
from flask import Flask, request, jsonify, make_response
from flask_restful import Resource, Api, reqparse
from flask_httpauth import HTTPTokenAuth
from schema import Schema, And, Or, Use, Optional, SchemaError
import bleach
import dotenv
from dotenv import load_dotenv
from bcj_ai import BCJAIapi as ai, BCJStatus
from helper import Validator, Message
from db import Database, DuplicateKeyError


load_dotenv()
secret_token = os.getenv('SECRET_TOKEN')
app = Flask(__name__, instance_relative_config=True)
api = Api(app)
validator = Validator()
ai = ai()
auth = HTTPTokenAuth(scheme="Bearer")



@auth.verify_token
def verify_token(token):
    """
    Authentication method for the enviroment using this service
    via SECRET_TOKEN
    """
    if token==secret_token:
        return token
    return None
class Bug(Resource):
    """
    Web service class for working with a usability problem (UP)
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
            validator.validate_data_get(req) #Validate the JSON
        except(SchemaError, ValueError):
            return make_response(jsonify({"message": Message.FAILURE.value}), 400)

        try:
            bugs = ai.get_similar_bugs_k(**req)
        except ValueError:
            return make_response(jsonify({'message': Message.NO_USER.value}),404)
        except AssertionError:
            return make_response(jsonify({'message': Message.UNFULFILLED_REQ.value}), 400)
        return make_response(jsonify(data=bugs[1]),bugs[0].value)

    @auth.login_required
    def post(self):
        """
        Method for handling POST request on '/bug',
        used for inserting a UP to the AI and its database.

        Returns
        -------
        A message with a brief description explaining the result for the request and status code.
        """

        req = request.json
        try:
            validator.validate_data(req)
        except(SchemaError, ValueError):
            return make_response(jsonify({'message': Message.FAILURE.value}),400)

        try:
            status, message = ai.add_bug(**req)
        except(TypeError, DuplicateKeyError):
            return make_response(jsonify({'message': Message.NO_USER.value}),404)
        except AssertionError:
            return make_response(jsonify({'message': Message.UNFULFILLED_REQ.value}),404)

        return make_response(jsonify(data={'message': message.value}), status.value)

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


        try:
            status, message = ai.update_bug(**req)
        except ValueError:
            return make_response(jsonify({'message': Message.NO_USER.value}),404)

        return make_response(jsonify({'message': message.value}), status.value)

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

        try:
            status, message = ai.remove_bug(_id=req['id'],user_id=req['user_id'])
        except ValueError:
            return make_response(jsonify({'message': Message.NO_USER.value}),404)

        return make_response(jsonify({'message': message.value}), status.value)

class Batch(Resource):
    """
    Web service class for working with a batch of bugs
    """

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
            validator.validate_batch_id(req)
        except(SchemaError, ValueError):
            return {'message': Message.FAILURE.value},400

        try:
            status, message = ai.remove_batch(batch_id=req['batch_id'],user_id=req['user_id'])
        except ValueError:
            return make_response(jsonify({'message': Message.NO_USER.value}),404)

        return make_response(jsonify({'message': message.value}), status.value)

    @auth.login_required
    def post(self):
        """
        Method for handling a post request on '/batch'.
        Used for inserting multiple examples at once.

        Returns
        -------
        Message with brief explanation and status code
        """
        
        try:
            req = request.json
            user_id = req['user_id'] if 'user_id' in req else None
            list_of_json = req['data'] if 'data' in req else None
            if not user_id or not list_of_json:
                raise ValueError('User_id and data required')

            if not isinstance(list_of_json,list):
                raise ValueError
            [validator.validate_batch_data(los) for los in list_of_json]
        except ValueError:
            return make_response(jsonify({'message': Message.FAILURE.value}),400)

        try:
            status, message = ai.add_batch(**req)
        except ValueError:
            return make_response(jsonify({'message': Message.NO_USER.value}),404)
        except AssertionError:
            return make_response(jsonify({'message': 'All batch_id must be the same'}),
                400)
        return make_response(jsonify(data={'message': message.value}),
                                    status.value)

api.add_resource(Bug,'/bug')
api.add_resource(Batch, '/batch')
