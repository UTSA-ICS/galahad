import dataset
import time
import datetime

class UserDatabase:
	def __init__(self):
		self._username = None
		self._authorizedRoleIds = None
		self._userToken = None
		self._db = dataset.connect('sqlite:////home/kelli/galahad/canvas/Database/canvas.db')
		self._table = self._db['USER']

	def set_user(self, userToken):
		self._userToken = userToken

	def set_values(self, values_json):
		self._username = values_json['USERNAME']
		self._authorizedRoleIds = values_json['AUTHORIZEDROLEIDS']
		
	def insert(self):
		if self._userToken == None:
			self._userToken = 'temp'
		d = {
			'USERNAME'				: self._username,
			'AUTHORIZEDROLEIDS'		: self._authorizedRoleIds,
			'USERTOKEN'				: self._userToken,
		}
		self._table.upsert(d,['USERTOKEN'])
		return self._userToken

	def find_one(self):
		return self._table.find_one(USERTOKEN=self._userToken)

	def find_all(self):
		users = []
		data = self._table.all()
		for user in data:
			users.append(user)
		return users

if __name__ == '__main__':
	user = UserDatabase()
	user.set_user('temp')
	print user.find_one()
	print user.find_all()
