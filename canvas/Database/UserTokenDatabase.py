import	dataset
import	time
import	datetime

class UserTokenDatabase:
	def __init__(self):
		self._username = None
		self._token = None
		self._expiration = None

	def set_values(self, values_json):
		self._username = values_json['USERNAME']
		self._token = values_json['TOKEN']  # create using OneLogin?
		self._expiration = values_json['EXPIRATION']

	def insert(self):
		d = {
			'USERNAME'		: self._username,
			'TOKEN'			: self._token,
			'EXPIRATION'	: self._expiration,
		}
		self._table.insert(d)
		return self._token

	def retrieve(self, token):
		return self._table.find_one(TOKEN=token)
