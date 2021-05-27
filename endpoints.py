from flask import Flask
from flask_restful import Resource, Api, reqparse
import pandas as pandas
import ast

app = Flask(__name__)
api = Api(app)

class Bug(Resource):

    pass

class BugBatch(Resource):

    pass


api.add_resource(Bug,'/bug')
api.add_resource(BugBatch, '/bug-batch')

if __name__ =='__main__':
    app.run()