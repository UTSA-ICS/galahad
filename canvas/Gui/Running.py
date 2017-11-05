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

		self.formset = ['_virtueList','||','_textArea']

		self._virtueList.horizontal_headers = ['VirtueId','State']
		self._virtueList.readonly = True
		self._virtueList.select_entire_row = True

		self._virtueList.cell_double_clicked_event = self.__clicked

		self._vlist = User().virtuelist('kelli')
		
		for v in self._vlist:
			self._virtueList += [v['VIRTID'],v['STATE']]

	def __clicked(self,row,column):
	
		val = self._virtueList.get_value(0,row)
	
		for v in self._vlist:
			if v['VIRTID'] == val:
				self._textArea.value =  "" 	+ \
					"VIRTID			: " + str(v['VIRTID']) + \
					"\nROLEID			: "	+ str(v['ROLEID']) + \
					"\nAPPLICATIONIDS		: " + str(v['APPLICATIONIDS']) + \
					"\nSTATE			: " + str(v['STATE'])
				break

		"""
		if self._virtueList.horizontal_headers[column] == 'ID':
			self._virtueList.set_value(column,
								   row,
								   'clicked')
		"""

if __name__ == "__main__":	pyforms.start_app( Running )
