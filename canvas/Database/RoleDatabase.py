import	dataset
import	time
import	datetime

class RoleDatabase:
	def __init__(self):
		self._roleId = None
		self._name = None
		self._applicationIds = None
		self._startingResourceIds = None
		self._startingTransducerIds = None
		self._version = None	
		self._userToken = None
		self._db = dataset.connect('sqlite:////home/kelli/galahad/canvas/Database/canvas.db')
		self._table = self._db['ROLE']

	def set_user(self, userToken):
		self._userToken = userToken

	def set_values(self, values_json):
		self._name = values_json['NAME']
		self._applicationIds = values_json['APPLICATIONIDS']
		self._startingResourceIds = values_json['STARTINGRESOURCEIDS']
		self._startingTransducerIds = values_json['STARTINGTRANSDUCERIDS']

		self._roleId = self._name.replace(" ","") + str(int(time.time()))
		self._version = datetime.date.today()

	def insert(self):
		d = {
			'ROLEID'				: self._roleId,
			'NAME'					: self._name,
			'VERSION'				: self._version,
			'APPLICATIONIDS'		: self._applicationIds,
			'STARTINGRESOURCEIDS'	: self._startingResourceIds,
			'STARTINGTRANSDUCERIDS'	: self._startingTransducerIds,
			'USERTOKEN'				: self._userToken,
		}
		self._table.insert(d)
		return self._roleId

	def find_one(self, roleId):
		return self._table.find_one(USERTOKEN=self._userToken,
									ROLEID=roleId)

	def find_all(self):
		roles = []
		data = self._table.all()
		for role in data:
			roles.append(role)
		return roles

if __name__ == "__main__":
	from ApplicationDatabase		import ApplicationDatabase

	app = ApplicationDatabase()
	app.set_user('kelli')
	app.set_values({'NAME':'firefox', 'OS':'LINUX'})
	appId = app.insert()

	role = RoleDatabase()
	role.set_user('kelli')
	role.set_values({	'NAME'					: 'User',
						'APPLICATIONIDS'		: appId,
						'STARTINGRESOURCEIDS'	: '',
						'STARTINGTRANSDUCERIDS'	: '', })
	roleId = role.insert()
	print(role.find_one(roleId))
	print(role.find_all())
