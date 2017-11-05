from	__init__			import *
from	pyforms.Controls			import ControlCombo

class New(BaseWidget):
	"""
	This class manages GUI Virtue creation.
	"""

	def __init__(self):
		BaseWidget.__init__(self)

		self._list = ControlCombo()
		items = ['FIREFOX','INTERNET_EXPLORER','MICROSOFT_WORD','CALC',
				 'WINDOWS_CMD','TERMINAL','LIBREOFFICE_IMPRESS',
				 'LIBREOFFICE_WRITER','LIBREOFFICE_CALC','MAIL']
		for item in items:
			self._list.add_item(item)

		self._new = ControlButton('Start')
		self._new.value = self.__launch

		self.formset = ['_list','||','_new']

	def __launch(self):
		self._new.label = 'Success!'

if __name__ == "__main__":	pyforms.start_app( New )
