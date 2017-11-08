from	__init__			import *
from	Virtue				import Virtue
from	User				import User

class Running(BaseWidget):
	"""
	This class displays all running Virtues in a list format.
	"""

	def __init__(self):
		BaseWidget.__init__(self,'Running')

		self._virtueList = ControlList('Running Virtues')
		self._textArea = ControlTextArea(' ')

		self._stop = ControlButton('Stop')
		self._stop.value = self.__stop

		self.formset = ['_virtueList','||', 
							('_textArea','=','_stop','=',' ',)]

		self._virtueList.horizontal_headers = ['VirtueId','State']
		self._virtueList.readonly = True
		self._virtueList.select_entire_row = True

		self._virtueList.cell_double_clicked_event = self.__clicked

		self._vlist = User().virtuelist('kelli')
		
		for v in self._vlist:
			self._virtueList += [v['VIRTID'],v['STATE']]

		self._virtue = None

	def __clicked(self,row,column):
	
		val = self._virtueList.get_value(0,row)
	
		for v in self._vlist:
			if v['VIRTID'] == val:
				self._virtue = v
				self._textArea.value =  "" 	+ \
					"VIRTID			: " + str(v['VIRTID']) + \
					"\nROLEID			: "	+ str(v['ROLEID']) + \
					"\nAPPLICATIONIDS		: " + str(v['APPLICATIONIDS']) + \
					"\nSTATE			: " + str(v['STATE'])
				break

	def __stop(self):
		if self._virtue == None:
			self._textArea.value = "Error: No Virtue Selected"
		else:
			self._textArea.value = self._virtue
			for app in self._virtue['APPLICATIONIDS']:
				self._textArea.append(app + ' stopped\n')


if __name__ == "__main__":	pyforms.start_app( Running )
