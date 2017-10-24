from	collections			import OrderedDict

d = {}
d['application'] = {
	'get'		:	[1,0,0,1],
}
d['role'] = {
	'get'		:	[0,0,1,1],
}
d['virtue'] = {
	'get'					:	[0,0,0,0,1,1],
	'create'				:	[0,0,1,0,1,0],
	'launch'				:	[0,0,0,0,1,1],
	'stop'					:	[0,0,0,0,1,1],
	'destroy'				:	[0,0,0,0,1,1],
	'application launch'	:	[1,0,0,0,1,1],
	'application stop'		:	[1,0,0,0,1,1],
}
d['user'] = {
	'login'					:	[0,1,1,0,0,1],
	'logout'				:	[0,0,0,0,1,0],
	'role list'				:	[0,0,0,0,1,0],
	'virtue list'			:	[0,0,0,0,1,0],
}	
	

class CheckUserAPI:

	def __init__(self):
		pass
		
	def _flatten(self, args):
		comp = []
		od = OrderedDict(sorted(args.items(), key=lambda t: t[0]))
		for item in od:
			if od[item]==None:
				comp.append(1)
			else:
				comp.append(0)
		return comp

	def _mult(self, comp, key):
		result = 0
		for i in xrange(len(comp)):
			result += comp[i]*key[i]
		return result

	def calc(self, args):
		comp = self._flatten(args)
		key = d[args['subparser']]
		result = self._mult(comp, key[args['command']])
		if result > 0:	return 1
		return 0
