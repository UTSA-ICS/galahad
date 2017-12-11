import pymongo
from pymongo import MongoClient

client = pymongo.MongoClient()
collection = client.excalibur.usertokens

class UserToken(object):

    def __init__(self, data):
	self.username = data.get('username', '')
	self.token = data.get('token', '')
	self.expiration = data.get('expiration', '')

    def list(self):
	return 254
