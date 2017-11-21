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


	"""
	API Defined
	"""

	# User
	# Gets information about the indicated Role.
	# Return -> Information about the indicated Role.
	# Type -> Role
	def get(self, userToken, roleId):
		role = RoleDatabase()
		role.set_user(userToken)
		return role.find_one(roleId)

	# Admin
	# Creates a new Role with the given parameters.
	# Return -> The newly created Role, with ID.
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
	# Return -> All the Roles, with IDs.
	# Type -> list of Role
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
