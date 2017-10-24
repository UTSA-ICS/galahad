import	dataset
import	json
import	time
import	datetime

from	Application				import Application

class Role:
	ROLEID = ''					# Required - False		# Type -> String
	NAME = ''					# Required - True		# Type -> String
	VERSION = ''				# Required - True		# Type -> String
	APPLICATIONIDS = []			# Required - True		# Type -> set of String
	STARTINGRESOURCEIDS = []  	# Required - True		# Type -> set of String
	STARTINGTRANSDUCERIDS = []	# Required - True		# Type -> set of String


	def __init__(self):
		pass

	def add(self, name):
		app = Application()
		apps = self.APPLICATIONIDS
		apps.append(app.create(name))
		self.APPLICATIONIDS = apps
		db = dataset.connect('sqlite:///canvas.db')
		table = db['role']
		table.update({
			'ROLEID'			: self.ROLEID,
			'APPLICATIONIDS'	: self.converttostring(self.APPLICATIONIDS),
		}, ['ROLEID'])
		return 0

	def converttostring(self, dlist):
		return ','.join(str(x) for x in dlist)
	
	def converttolist(self, string):
		return [str(x) for x in string.split(",")]

	def converttodb(self, d):
		return {
			'ROLEID'				:	d['ROLEID'],
			'NAME'					:	d['NAME'],
			'VERSION'				:	d['VERSION'],
			'APPLICATIONIDS'		:	self.converttostring(d['APPLICATIONIDS']),
			'STARTINGRESOURCEIDS'	:	self.converttostring(d['STARTINGRESOURCEIDS']),
			'STARTINGTRANSDUCERIDS'	:	self.converttostring(d['STARTINGTRANSDUCERIDS']),
		}

	def convertfromdb(self, d):
		return {
			'ROLEID'				:	d['ROLEID'],
			'NAME'					:	d['NAME'],
			'VERSION'				:	d['VERSION'],
			'APPLICATIONIDS'		:	self.converttolist(d['APPLICATIONIDS']),
			'STARTINGRESOURCEIDS'	:	self.converttolist(d['STARTINGRESOURCEIDS']),
			'STARTINGTRANSDUCERIDS'	:	self.converttolist(d['STARTINGTRANSDUCERIDS']),
		}

	"""
	API Defined
	"""
	def get(self, userToken, roleId):
		db = dataset.connect('sqlite:///canvas.db')
		table = db['role']
		role = table.find_one(ROLEID=roleId)
		
		return json.dumps(self.convertfromdb(role))

	def create(self, userToken, role):
		db = dataset.connect('sqlite:///canvas.db')
		table = db['role']
		roled = json.loads(role)
		if roled['ROLEID'] is None:
			roled['ROLEID'] = roled['NAME'].replace(" ","") + str(int(time.time()))
		if roled['VERSION'] is None:
			roled['VERSION'] = str(datetime.datetime.now())
		self.ROLEID 				= roled['ROLEID']
		self.NAME					= roled['NAME']
		self.VERSION				= roled['VERSION']
		self.APPLICATIONIDS			= roled['APPLICATIONIDS']
		self.STARTINGRESOURCEIDS	= roled['STARTINGRESOURCEIDS']
		self.STARTINGTRANSDUCERIDS	= roled['STARTINGTRANSDUCERIDS']

		table.insert(self.converttodb(roled))
		return json.dumps(roled)

	def list(self):
		roles = []
		db = dataset.connect('sqlite:///canvas.db')
		result = db['role'].all()
		for role in result:
			roles.append(json.dumps(self.convertfromdb(role)))
		return roles


if __name__ == "__main__":
	role = Role()
	role.create('kelli', json.dumps(
		{
			'ROLEID'				: None,
			'NAME'					: 'Database Administrator',
			'VERSION'				: None,
			'APPLICATIONIDS'		: [],
			'STARTINGRESOURCEIDS'	: [],
			'STARTINGTRANSDUCERIDS'	: [],
		})
	)
	role.add('xterm')
	role.add('firefox')
	print(role.get('kelli', role.ROLEID))
	print(role.list())
