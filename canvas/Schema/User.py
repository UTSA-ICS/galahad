import	dataset
import	json

from	__init__				import *
from	Virtue					import Virtue
from	UserToken				import UserToken

from	VirtueDatabase			import VirtueDatabase

class User:
	USERNAME = None				# Required - True		# Type -> String
	AUTHORIZEDROLEIDS = None	# Required - True		# Type -> set of String


	def __init__(self):
		pass

	"""
	API Defined
	"""

	# User
	# Logs in a User with a username and password
	# Return -> The UserToken to be used for subsequent authorization
	# calls.
	# Type -> UserToken
	def login(self, username, credentials, forceLogoutOfOtherSessions):
		return 254 		# return UserToken

	# User / Admin
	# Logs out the User identified by the given UserToken.
	# Type -> return code
	def logout(self, userToken, username=None):
		return 254

	# User
	# Lists the Roles available to the given User.
	# Return -> A set of Roles to the given User.
	# Type -> set of Role
	def rolelist(self, userToken):
		return 254		# return set of Role
		# implement Role.list() so that returns username filtered list 

	# User / Admin
	# Lists the current Virtue instantiations for the given User.
	# Return -> A set of Virtues for the given User.
	# Type -> set of Virtue
	def virtuelist(self, userToken, username=None):
		# return 254		# return set of Virtue
		if username==None:
			username = UserToken().getusername(userToken)
		virts = Virtue().getvirtuesfromuser(username)
		virt = VirtueDatabase()
		virt.set_user(username)
		return virt.find_all()

	# Admin
	# Lists all Users currently present in the system.
	# Return -> All the Users, with IDs.
	# Type -> list of User
	def list(self, userToken):
		#return 254		# return list of User
		users = []
		db = dataset.connect('sqlite:///canvas.db')
		users = db['user'].all()
		for user in users:
			users.append(json.dumps(user))
		return users

	# Admin
	# Gets information about the indicated User.
	# Return -> Information about the indicated User.
	# Type -> User
	def get(self, userToken, username):
		#return 254		# return User
		db = dataset.connect('sqlite:///canvas.db')
		table = db['user']
		row = table.find_one(USERNAME=username)
		return json.dumps(row)

	# Admin
	# Authorizes the indicated Role for the given User. This should also
	# post a message to the User to let them know what happened.
	# Return -> Information about the indicated User.
	# Type -> User
	def roleauthorize(self, userToken, username, roleId):
		#return 254		# return User
		db = dataset.connect('sqlite:///canvas.db')
		table = db['user']
		row = table.find_one(USERNAME=username)
		self.USERNAME = username
		self.AUTHORIZEDIDS = json.loads(row['LIST'])
		self.AUTHORIZEDIDS.append(roleId)
		d = {
			'USERNAME'			:	username,
			'AUTHORIZEDROLEIDS'	:	json.dumps(self.AUTHORIZEDIDS),
		}
		table.update(d, ['USERNAME'])
		return json.dumps(d)

	# Admin
	# Unathorizes the indicated Role for the given User.
	# Return -> Information about the indicated User.
	# Type -> User
	def roleunauthorize(self, userToken, username, roleId):
		#return 254		# return User
		db = dataset.connect('sqlite:///canvas.db')
		table = db['user']
		row = table.find_one(USERNAME=username)
		ids = json.loads(row['LIST'])
		ids.remove(roleId)
		d = {
			'USERNAME'			:	username,
			'AUTHORIZEDROLEIDS'	:	json.dumps(ids),
		}
		table.update(d, ['USERNAME'])
		return json.dumps(d)

if __name__ == "__main__":	print(User().virtuelist('kelli'))
