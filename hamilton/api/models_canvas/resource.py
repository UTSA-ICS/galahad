import pymongo
from pymongo import MongoClient

client = pymongo.MongoClient()
collection = client.excalibur.resources

class Resource(object):

	def __init__(self, data):
		self.id = data.get('id', None)
		self.type = data.get('type', '')
		self.unc = data.get('unc', '')
		self.credentials = data.get('credentials', None)

	def get(self):
		return 254

	def list(self):
		return 254

	def attach(self):
		return 254

	def detach(self):
		return 254
