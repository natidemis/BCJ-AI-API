from flask import Flask, request
from flask_restful import Resource, Api, reqparse
import pandas as pandas
import ast
from bcj_ai import BCJAIapi as ai

app = Flask(__name__, instance_relative_config=True)
api = Api(app)
app.config.from_object('config')

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