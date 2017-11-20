import	dataset
import	time
import	datetime

class ApplicationDatabase:
	def __init__(self):
		self._applicationId = None
		self._name = None
		self._version = None
		self._os = None
		self._userToken = None
		self._db = dataset.connect('sqlite:////home/kelli/galahad/canvas/Database/canvas.db')
		self._table = self._db['APPLICATION']

	def set_user(self, userToken):
		self._userToken = userToken

	def set_values(self, values_json):
		self._name = values_json['NAME']
		self._os = values_json['OS']

		self._version = str(datetime.date.today())
		self._applicationId = self._name + str(int(time.time()))

	def insert(self):
		d = {
			'APPID'		: self._applicationId,
			'NAME'		: self._name,
			'VERSION'	: self._version,
			'OS'		: self._os,
			'USERTOKEN'	: self._userToken,
		}
		self._table.upsert(d,['APPID'])
		return self._applicationId

	def find_one(self, applicationId):
		return self._table.find_one(USERTOKEN=self._userToken,
									APPID=applicationId)

	def find_all(self):
		# verify userToken admin access
		apps = []
		data = self._table.all()
		for app in data:
			apps.append(app)
		return apps

if __name__ == "__main__":
	app = ApplicationDatabase()
	app.set_user('kelli')
	app.set_values({'NAME':'firefox', 'OS':'LINUX'})
	appId = app.insert()
	print(app.find_one(appId))
	print(app.find_all())
