from	collections			import OrderedDict

d = {}
d['logging'] = {
	'components get'		:	[0,0,0,0,0,1,0],
	'events get'			:	[1,1,0,1,0,1,1],
}	
	

class CheckSecurityAPI:

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
