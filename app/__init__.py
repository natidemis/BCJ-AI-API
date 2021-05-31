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
        bugs = ai.get_similar_bugs_k(req['summary'], req['description'], req['k'])
        if bugs[0].value == 200:
            return bugs[1],bugs[0].value
        return bugs[1],bugs[0].value
    
    def post(self):
        data = request.json
<<<<<<< HEAD
        print(data)
        #if ai.add
=======
        error = "Input data was in incorrect format"
        try:
            if data['summary'] and data['description'] and data['structured_info']:
                info = data['structured_info']
                if info['id'] and info['creationDate']:
                    if ai.add_bug(data,summary=data['summary'], description =data['description'], structured_info=data['structured_info']) == 200:
                        return {"message": "Succeeded"},200
                    else:
                        return {"message": error}, 400
        except:
            return {"message": error}, 401
>>>>>>> 9c791c882ac41a6424bb97427a1e47f37e6e5860
        pass
    
    def patch(self):
        pass
    
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