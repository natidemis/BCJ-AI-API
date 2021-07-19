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

load_dotenv()
SECRET_TOKEN = os.getenv('SECRET_TOKEN')
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
    if token==SECRET_TOKEN:
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

        if len(req['summary']) > 0 or len(req['description'])>0:
            status, message = ai.add_bug(
                                        summary=bleach.clean(req['summary']),
                                        description=bleach.clean(req['description']),
                                        structured_info=req['structured_info'])
            return make_response(jsonify(data={'message': message.value}), status.value)

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
        status, message = ai.update_bug(
                                        summary=summary,
                                        description = description,
                                        structured_info = req['structured_info'])
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
        status, message = ai.remove_bug(req['id'])
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

        status, message = ai.remove_batch(req['batch_id'])
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
        req = request.json
        data = []
        try:
            if not isinstance(req,list):
                raise ValueError
            validator.validate_batch_data(req[0])
            batch_id = req[0]['structured_info']['batch_id']
            for item in req:
                validator.validate_batch_data(item)
                if batch_id != item['structured_info']['batch_id']:
                    raise ValueError('All batch_id must be the same')
                if len(item['summary']) > 0 or len(item['description'])>0:
                    data.append({
                        "id": item['structured_info']['id'],
                        "summary": bleach.clean(item['summary']),
                        "description": bleach.clean(item['description']),
                        "batch_id": item['structured_info']['batch_id'],
                        "date": item['structured_info']['date']
                    })
                else:
                    raise ValueError('Both summary and description may not have string length of 0')
        except(SchemaError, ValueError):
            return make_response(jsonify({'message': Message.FAILURE.value}),400)

        status, message = ai.add_batch(data)           
        return make_response(jsonify(
                                    data={'message': message.value}), status.value)

api.add_resource(Bug,'/bug')
api.add_resource(Batch, '/batch')
