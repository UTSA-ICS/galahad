from	collections			import OrderedDict

d = {}
d['application'] = {
	'list'					:	[0,0,1],
}
d['role'] = {
	'create'				:	[0,1,0,1],
	'list'					:	[0,0,0,1],
}
d['resource'] = {
	'get'					:	[0,1,0,1,0],
	'list'					:	[0,0,0,1,0],
	'attach'				:	[0,1,0,1,1],
	'detach'				:	[0,1,0,1,1],
}
d['user'] = {
	'list'					:	[0,0,0,1,0],
	'get'					:	[0,0,0,1,1],
	'virtue list'			:	[0,0,0,1,1],
	'logout'				:	[0,0,0,1,1],
	'role authorize'		:	[0,1,0,1,1],
	'role unauthorize'		:	[0,1,0,1,1],
}
d['system'] = {
	'export'				:	[0,0,0,1],
	'import'				:	[0,1,0,1],
}
d['test'] = {
	'import user'			:	[0,0,1,1],
	'import application'	:	[0,0,1,1],
	'import role'			:	[0,0,1,1],
}
d['usertoken'] = {
	'list'					:	[0,0,1],
}
	

class CheckAdminAPI:

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
