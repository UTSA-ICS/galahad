import pymongo
from pymongo import MongoClient

client = pymongo.MongoClient()
collection = client.excalibur.roles

class Role(object):

    def __init__(self, data):
	self.id = data.get('id', None)
	self.name = data.get('name', '')
	self.version = data.get('version', '')
	self.application_ids = data.get('application_ids', None)
	self.starting_resource_ids = data.get('starting_resource_ids', None)
	self.starting_transducer_ids = data.get('starting_transducer_ids', None)

    def create(self):
	return 254

    def list(self):
	return 254
