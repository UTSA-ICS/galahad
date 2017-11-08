from	__init__			import *
from	pyforms.Controls	import ControlEmptyWidget

from	Running				import Running
from	New					import New

class Window(Running, New, BaseWidget):
	"""
	This application is a GUI implementation of the Canvas architecture.
	"""

	def __init__(self):
		Running.__init__(self)
		New.__init__(self)
		BaseWidget.__init__(self, 'Window')

		self._panelR = ControlEmptyWidget()
		self._panelN = ControlEmptyWidget()

		winR = Running()
		winR.parent = self
		self._panelR.value = winR

		winN = New()
		winN.parent = self
		self._panelN.value = winN

		self.formset = ['_panelR', '=', '_panelN']


if __name__ == "__main__":	pyforms.start_app( Window )
