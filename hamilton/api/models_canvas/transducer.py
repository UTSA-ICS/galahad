import pymongo
from pymongo import MongoClient

client = pymongo.MongoClient()
collection = client.excalibur.transducers

class Transducer(object):

    def __init__(self, data):
	self.id = data.get('id', None)
	self.name = data.get('name', '')
	self.type = data.get('type', '')
	self.start_enabled = data.get('start_enabled', None)
	self.starting_configuration = data.get('starting_configuration', None)
	self.required_access = data.get('required_access', None)

    def list(self):
	return 254

    def get(self):
	return 254

    def enable(self):
	return 254

    def disable(self):
	return 254

    def get_enabled(self):
	return 254

    def get_configuration(self):
	return 254

    def list_enabled(self):
	return 254
