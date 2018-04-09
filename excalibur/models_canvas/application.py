import pymongo
from pymongo import MongoClient

client = pymongo.MongoClient()
collection = client.excalibur.applications

class Application(object):

	def __init__(self, data):
		self.id = data.get('id', None)
		self.name = data.get('name', '')
		self.version = data.get('version', '')
		self.os = data.get('os', '')

	def insert(self):
		#return 254
		data = {
			'id': self.id,
			'name': self.name,
			'version': self.version,
			'os': self.os
		}
		collection.insert(data)
		return 0

	def update(self, query, data):
		#return 254
		collection.update(query, data)
		return 0

    """ API Defined """

	def get(self,query):
		#return 254
		return collection.find_one(query)

	def list(self):
		#return 254
		return collection.find()

if __name__ == '__main__':
    """
    app = Application({'id':123, 'name':'firefox', 'version':1, 'os':'Linux'})
    print app.insert()
    """

    """
    app = Application({})
    print app.get({"id":123})
    for item in app.list():
		print item
    """

    app = Application({})
    print app.get({'id':123})
    app.update(
		{ "id": 123 },
		{
	    	'id': 123,
	    	'name': 'firefox',
	    	'version': 2,
	    	'os': 'Linux'
		}
    )
    print app.get({'id':123})
