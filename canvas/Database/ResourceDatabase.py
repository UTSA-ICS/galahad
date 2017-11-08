import	dataset
import	time
import	datetime

class ResourceDatabase:
	def __init__(self):
		self._resourceId = None
		self._type = None					# [DRIVE, PRINTER]
		self._uac = None
		self._credentials = None
		self._userToken = None
		self._db = dataset.connect('sqlite:///canvas.db')
		self._table = self._db['RESOURCE']

	def set_user(self, userToken):
		self._userToken = userToken

	def set_values(self, values_json):
		self._type = values_json['TYPE']
		self._uac = values_json['TYPE']
		self._credentials = '' # interact with OneLogin - need to look into

		self._resourceId = self._type + str(int(time.time()))

	def insert(self):
		d = {
			'RESID'					: self._resourceId,
			'TYPE'					: self._type,
			'UAC'					: self._uac,
			'CREDENTIALS'			: self._credentials,
			'USERTOKEN'				: self._userToken,
		}
		self._table.insert(d)
		return self._resourceId

	def find_one(self, resourceId):
		return self._table.find_one(USERTOKEN=self._userToken,
									RESID=resourceId)

	def find_all(self):
		return self._table.find(USERTOKEN=self._userToken)

if __name__ == "__main__":
	res = ResourceDatabase()
	res.set_user('kelli')
	res.set_values({	'TYPE'			: 'DRIVE',
						'UAC'			: 'abc', 	})
	resId = res.insert()
	print(res.find_one(resId))
	print(res.find_all())
