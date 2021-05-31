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
        print(Status.OK.value)
        #print(request.json) #Sækja json ur requesti..
        return {'ok': 'ok'},200


    #if results:
    #    return results,200
    #else:
    #    return {Lýsing á villu},404
    
    def post(self):
        data = request.json
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