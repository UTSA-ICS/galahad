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
		#return 254
		data = {
			'id': self.id,
			'name': self.name,
			'version': self.version,
			'application_ids': self.application_ids,
			'starting_resource_ids': self.starting_resource_ids,
			'starting_transducer_ids': self.starting_transducer_ids
		}
		collection.insert(data)
		return 0

	def list(self):
		#return 254
		return collection.find()

if __name__ == '__main__':
	role = Role({'id':123, 'name':'User', 'version':1, 'application_ids':[1,2,3],
				 'starting_resource_ids':[4,5,6], 'starting_transducer_ids':[7,8,9]})
	role.create()
	for item in role.list():
		print item
