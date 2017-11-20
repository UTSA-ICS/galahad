#from pymongo import MongoClient
from pprint import pprint

# connect to MongoDB
#client = MongoClient("mongodb://127.0.0.1:27017")


# Issue the serverStatus command and print the results
#serverStatusResult=client.admin.command("serverStatus")
#pprint(serverStatusResult)

import dataset
db = dataset.connect('mysql://root:test123@localhost/')
test = db['test']

from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
	return 'Welcome to Excalibur.'

@app.route('/virtues')
def virtues():
	return "Virtues"

#virtues = client.virtues.find()
#pprint(virtues)
