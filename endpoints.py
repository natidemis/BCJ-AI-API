from flask import Flask
from flask_restful import Resource, Api, reqparse
import pandas as pandas
import ast

app = Flask(__name__)
api = Api(app)

class Bug(Resource):
    def get(self):
    
    results = #Kalla á gervigreindina og sækja k-villur í json formatti
    
    if results:
        return results,200
    else:
        return {Lýsing á villu},404
    
    def post(self):
        
class BugBatch(Resource):

    pass


api.add_resource(Bug,'/bug')
api.add_resource(BugBatch, '/bug-batch')

if __name__ =='__main__':
    app.run()