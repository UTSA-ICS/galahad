import	json
from	Application			import Application

class ApplicationArguments:
	def __init__(self):
		pass

	def application(self,args):
		app = Application()
		app.APPID = args['applicationId']

		self_to_call = getattr(self, args['command'])
		method_to_call = getattr(app, args['command'])
		result = self_to_call(method_to_call, args)
		#print(result)
		return(result)

	def save(self, method_to_call, args):
		result = method_to_call()
		return result

	def get(self, method_to_call, args):
		result = method_to_call(args['userToken'], args['applicationId'])
		return result

	def list(self, method_to_call, args):
		result = method_to_call(args['userToken'])
		return result

if __name__ == "__main__":
		appargs = {
			'command'		:	'list',
			'userToken'		:	'kelli',
			'applicationId'	:	'765',
			'name'			:	'xterm',
			'version'		:	'2.3',
			'os'			:	'LINUX',
		}
		ApplicationArguments.application(ApplicationArguments(appargs), appargs)	
