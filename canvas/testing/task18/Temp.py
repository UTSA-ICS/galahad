import	os
import	json

class Process(object):
	def __init__(self, proc):
		self.text = 'Start Me'
		self._proc = proc
		
	def getText():
		#os.system("xpra start ssh/kelli@kelli-test-xpra2 --start-child=/usr/bin/firefox")
		#os.system("xpra start ssh/kelli@kelli-test-xpra2 --start-child=" + self._proc)
		d = {
			'status':'start',
			'serveruser':'kelli',
			'serverhost':'kelli-test-xpra2',
			'resource': self._proc,
		}
		return json.dumps(d)


#if __name__ == "__main__":	pyforms.start_app( Firefox )
