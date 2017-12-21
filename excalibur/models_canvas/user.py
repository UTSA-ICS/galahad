from dateutil import parser
import pymongo
from pymongo import MongoClient

client = pymongo.MongoClient()
collection = client.excalibur.users

class User(object):

	def __init__(self, data):
		self.username = data.get('username', '')
		self.authorized_role_ids = data.get('authorized_role_ids', None)

	def insert(self):
		data = {
			'username': self.username,
			'authorized_role_ids': self.authorized_role_ids,
		}
		collection.insert(data)
		return 0

	def update(self, query, data):
		#return 254
		collection.update(query, data)
		return 0

    """ API Defined """

	def login(self):
		return 254

	def logout(self):
		return 254

	def role_list(self):
		return 254

	def virtue_list(self):
		return 254

	def list(self):
		#return 254
		return collection.find()

	def get(self, query):
		#return 254
		return collection.find_one(query)

	def role_authorize(self, data):
		#return 254
		user = self.get({'username': data['username']})
		user['authorized_role_ids'].append(data['role_id'])
		return self.update({'username':user['username']},
			{ 'username':user['username'],
			  'authorized_role_ids':user['authorized_role_ids'] })

	def role_unauthorize(self, data):
		#return 254
		user = self.get({'username': data['username']})
		user['authorized_role_ids'].remove(data['role_id'])
		return self.update({'username':user['username']},
			{ 'username': user['username'],
			  'authorized_role_ids': user['authorized_role_ids'] })

if __name__ == '__main__':
	"""
	user = User({'username':'kelli', 'authorized_role_ids': [1,2,3]})
	print user.insert()
	"""

	user = User({})

	"""
	print user.get({'username':'kelli'})
	user.update(
		{'username':'kelli'},
		{
			'username':'kelli',
			'authorized_role_ids':[1,2,3,4]
		}
	)
	print user.get({'username':'kelli'})
	"""

	"""
	for item in user.list():
		print item 
	"""

	print user.role_authorize({'username':'kelli', 'role_id':6})
	print user.get({'username':'kelli'})

	user.role_unauthorize({'username':'kelli', 'role_id':6})
	print user.get({'username':'kelli'})
