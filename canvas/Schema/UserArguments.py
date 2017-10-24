import	json
from	User			import User

class UserArguments:
	def __init__(self):
		pass

	def user(self,args):
		usr = User()
		usr.USERNAME = args['username']
		
		self_to_call = getattr(self, args['command'])
		method_to_call = getattr(usr, args['command'])
		return self_to_call(method_to_call, args)


	def login(self, method_to_call, args):
		return method_to_call(args['username'], args['credentials'],
							  args['forceLogoutOfOtherSessions'])

	def logout(self, method_to_call, args):
		try:
			return method_to_call(args['userToken'], args['username'])
		except:
			return method_to_call(args['userToken'])

	def rolelist(self, method_to_call, args):
		return method_to_call(args['userToken'])

	def virtuelist(self, method_to_call, args):
		try:
			return method_to_call(args['userToken'], args['username'])
		except:
			return method_to_call(args['userToken'])

	def list(self, method_to_call, args):
		return method_to_call(args['userToken'])

	def get(self, method_to_call, args):
		return method_to_call(args['userToken'], args['username'])

	def roleauthorize(self, method_to_call, args):
		return method_to_call(args['userToken'], args['username'],
							  args['roleId'])

	def roleunauthorize(self, method_to_call, args):
		return method_to_call(args['userToken'], args['username'],
							  args['roleId'])
