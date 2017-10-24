import	json

class Process(object):
	def __init__(self, proc):
		self._proc		= proc

	def getText(self):
		d = {
			'status':'start',
			'serveruser':'kelli',
			'serverhose':'kelli-test-xpra2',
			'resource':self._proc,
		}
		return json.dumps(d)
