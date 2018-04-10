import pymongo
from pymongo import MongoClient

client = pymongo.MongoClient()
collection = client.excalibur.usertokens

class UserToken(object):

	def __init__(self, data):
		self.username = data.get('username', '')
		self.token = data.get('token', '')
		self.expiration = data.get('expiration', '')

	def insert(self):
		data = {
			'username': self.username,
			'token': self.token,
			'expiration': self.expiration
		}
		collection.insert(data)
		return 0

	def verify(self, data):
		if collection.find_one({'username': data['username']}):
			usertoken = collection.find_one({'username': data['username']})
			if data['token'] == usertoken['token']:
				return True
			else:
				return False
		else:
			return "No user " + data['username'] + " exists."

	def list(self):
		#return 254
		return collection.find()

if __name__ == '__main__':
	usertoken = UserToken({'username': 'kelli', 'token': 'abc123!', 'expiration':'now'})
	#usertoken.insert()
	print usertoken.verify({'username':'kelli', 'token':'abc123!'})
	print usertoken.verify({'username':'kelli', 'token':''})
	print usertoken.verify({'username':'bob', 'token':'abc123!'})
	for item in usertoken.list():
		print item
