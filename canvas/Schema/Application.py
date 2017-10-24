import	dataset
import	json
import	time
import	datetime

class Application:
	APPID = ''		# Required - False		# Type -> String
	NAME = ''		# Required - True		# Type -> String
	VERSION = ''	# Required - True		# Type -> String
	OS = ''			# Required - True		# Type -> String (enum)
											#		  [LINUX, WINDOWS]

	def __init__(self):
		pass

	def create(self, name):
		db = dataset.connect('sqlite:///canvas.db')
		table = db['application']
		self.NAME = name
		self.APPID = self.NAME + str(int(time.time()))
		self.VERSION = str(datetime.datetime.now())
		self.OS = 'LINUX'
		d = {
			'APPID'		:	self.APPID,
			'NAME'		:	self.NAME,
			'VERSION'	:	self.VERSION,
			'OS'		:	self.OS,
		}
		table.insert(d)
		return self.APPID	

	def get(self, userToken, applicationId):
		db = dataset.connect('sqlite:///canvas.db')
		table = db['application']
		app = table.find_one(APPID=applicationId)
		return json.dumps(app)

	def list(self, userToken):
		apps = []
		db = dataset.connect('sqlite:///canvas.db')
		result = db['application'].all()
		for app in result:
			apps.append(json.dumps(app))
		return apps
