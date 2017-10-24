import	json
import	dataset
import	pyforms
from	pyforms				import BaseWidget
from	pyforms.Controls	import ControlText
from	pyforms.Controls	import ControlButton

from	pysettings			import conf;
import	settings
conf+=	settings

from	Process				import Process

class JSONEncode(Process, BaseWidget):
	def __init__(self):
		Process.__init__(self, '')
		BaseWidget.__init__(self, 'JSONEncode window')
		self.parent = None

		self._text			= ControlText('Start Me')
		self._firefox		= ControlButton('Firefox')
		self._xterm			= ControlButton('Xterm')

		self._firefox.value	= lambda:self.launchProc("firefox")
		self._xterm.value 	= lambda:self.launchProc("xterm")

		self.formset = [ '_text', '_firefox','_xterm', ' ' ]

	def launchProc(self, text):
		self._proc = text
		self._text.value = text
		
		d = self.getText()
		self._text.value = d

		db = dataset.connect('sqlite:///xpra.db')
		table = db['xpra']
		table.insert(json.loads(d))

	def printText(self):
		print (self._text.value)


if __name__ == "__main__":	pyforms.start_app( JSONEncode )
