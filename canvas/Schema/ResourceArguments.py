import	json
from	Resource			import Resource

class ResourceArguments:
	def __init__(self, args):
		pass

	def resource(self, args):
		res = Resource()
		self_to_call = getattr(self, args['command'])
		method_to_call = getattr(res, args['command'])
		return self_to_call(method_to_call, args)

	def save(self, method_to_call, args):
		return method_to_call()

	def get(self, method_to_call, args):
		return method_to_call(args['userToken'], args['resourceId'])
	
	def list(self, method_to_call, args):
		return method_to_call(args['userToken'])

	def attach(self, method_to_call, args):
		return method_to_call(args['userToken'], args['resourceId'],
							  args['virtueId'])

	def detach(self, method_to_call, args):
		return method_to_call(args['userToken'], args['resourceId'],
							  args['virtueId'])


if __name__ == "__main__":
	resargs = {
		'command'		:	'list',
		'userToken'		:	'kelli',
		'resourceId'	:	'123',
		'type'			:	'DRIVE',
		'uac'			:	'value',
		'credentials'	:	'json string',
		'virtueId'		:	'456',
	}
	ResourceArguments.resource(ResourceArguments(resargs), resargs)
