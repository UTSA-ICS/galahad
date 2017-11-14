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

	def login(self, username, credentials, forceLogoutOfOtherSessians):
		return 254 		# return UserToken

	def logout(self, userToken, username=None):
		return 254

	def rolelist(self, userToken):
		return 254		# return set of Role
		# implement Role.list() so that returns username filtered list 

	def virtuelist(self, userToken, username=None):
		# return 254		# return set of Virtue
		if username==None:
			username = UserToken().getusername(userToken)
		virts = Virtue().getvirtuesfromuser(username)
		virt = VirtueDatabase()
		virt.set_user(username)
		return virt.find_all()

	def list(self, userToken):
		#return 254		# return list of User
		users = []
		db = dataset.connect('sqlite:///canvas.db')
		users = db['user'].all()
		for user in users:
			users.append(json.dumps(user))
		return users

	def get(self, userToken, username):
		#return 254		# return User
		db = dataset.connect('sqlite:///canvas.db')
		table = db['user']
		row = table.find_one(USERNAME=username)
		return json.dumps(row)

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
