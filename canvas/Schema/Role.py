import	dataset
import	json
import	time
import	datetime

from	__init__				import *
from	Application				import Application
from	RoleDatabase			import RoleDatabase

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

	# User
	# Gets information about the indicated Role.
	# Type -> Role
	def get(self, userToken, roleId):
		role = RoleDatabase()
		role.set_user(userToken)
		return role.find_one(roleId)

	# Admin
	# Creates a new Role with the given parameters.
	# Type -> Role
	def create(self, userToken, role):
		roled = RoleDatabase()
		roled.set_user(userToken)
		roled.set_values({
			'NAME'						: role['NAME'],
			'APPLICATIONIDS'			: role['APPLICATIONIDS'],
			'STARTINGRESOURCEIDS'		: role['STARTINGRESOURCEIDS'],
			'STARTINGTRANSDUCERIDS'		: role['STARTINGTRANSDUCERIDS'],
		})
		roleId = roled.insert()
		return roled.find_one(roleId)

	# Admin
	# List all Roles currently available in the system.
	def list(self):
		role = RoleDatabase()
		return role.find_all()


if __name__ == "__main__":
	role = Role()
	returned = role.create('kelli', {
		'NAME'						: 'Database Administrator',
		'APPLICATIONIDS'			: '',
		'STARTINGRESOURCEIDS'		: '',
		'STARTINGTRANSDUCERIDS'		: '',
	})
	print returned
