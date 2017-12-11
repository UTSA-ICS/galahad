from dateutil import parser
import pymongo
from pymongo import MongoClient

client = pymongo.MongoClient()
collection = client.excalibur.users

class User(object):

    def __init__(self, data):
        self.username = data.get('username', '')
	self.authorized_role_ids = data.get('authorized_role_ids', None)

    def login(self):
	return 254

    def logout(self):
	return 254

    def role_list(self):
	return 254

    def virtue_list(self):
	return 254

    def list(self):
	return 254

    def get(self):
	return 254

    def role_authorize(self):
	return 254

    def role_unauthorize(self):
	return 254
