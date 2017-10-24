import	json
from	Role					import Role
from	ApplicationArguments	import ApplicationArguments

class RoleArguments:
	def __init__(self):
		pass

	def role(self, args):
		ro = Role()
		self_to_call = getattr(self, args['command'])
		method_to_call = getattr(ro, args['command'])
		result = self_to_call(method_to_call, args)
		return(result)

	def save(self, method_to_call, args):
		return method_to_call()

	def get(self, method_to_call, args):
		return method_to_call(args['userToken'], args['roleId'])

	def create(self, method_to_call, args):
		return method_to_call()

	def list(self, method_to_call, args):
		return method_to_call()


if __name__ == "__main__":
		appargs = {
			'command'				:	'list',
			'userToken'				:	'kelli',
			'applicationId'			:	'',
			'name'					:	'',
			'version'				:	'',
			'os'					:	'',
		}
		appids = ApplicationArguments.application(ApplicationArguments(appargs), appargs)

		roleargs = {
			'command'				:	'list',
			'userToken'				:	'kelli',
			'roleId'				:	'453',
			'name'					:	'database admin',
			'version'				:	'0.1',
			'applicationIds'		:	json.dumps(appids),
			'startingResourceIds'	:	json.dumps(appids),
			'startingTransducerIds'	:	json.dumps(appids),
		}
		RoleArguments.role(RoleArguments(roleargs), roleargs)
