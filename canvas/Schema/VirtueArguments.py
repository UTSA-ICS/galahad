import	json
from	Virtue			import Virtue

class VirtueArguments:
	def __init__(self):
		pass

	def virtue(self, args):
		virt = Virtue()
		self_to_call = getattr(self, args['command'])
		method_to_call = getattr(virt, args['command'])
		return self_to_call(method_to_call, args)

	def save(self, method_to_call, args):
		return method_to_call()

	def get(self, method_to_call, args):
		return method_to_call(args['userToken'], args['virtueid'])

	def create(self, method_to_call, args):
		return method_to_call(args['userToken'], args['roleid'])

	def launch(self, method_to_call, args):
		return method_to_call(args['userToken'], args['virtueid'])

	def stop(self, method_to_call, args):
		return method_to_call(args['userToken'], args['virtueid'])

	def destroy(self, method_to_call, args):
		return method_to_call(args['userToken'], args['virtueid'])

	def applicationlaunch(self, method_to_call, args):
		return method_to_call(args['userToken'], args['virtueid'],
							  args['applicationid'])

	def applicationlaunch(self, method_to_call, args):
		return method_to_call(args['userToken'], args['virtueid'],
							  args['applicaitonid'])


if __name__ == "__main__":
	virtargs = {
		'command'				:	'get',
		'userToken'				:	'kelli',
		'virtueid'				:	'894',
		'username'				:	'kelli',
		'roleid'				:	'234',
		'applicationid'			:	'232',
		'applicationIds'		:	'id list',
		'resourceIds'			:	'resource list',
		'transducerIds'			:	'transducer list',
		'state'					:	'CREATING',
		'ipaddress'				:	'0.0.0.0',
	}
	VirtueArguments.virtue(VirtueArguments(virtargs), virtargs)	
