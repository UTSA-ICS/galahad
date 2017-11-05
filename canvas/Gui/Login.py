from	__init__			import *

class Login(BaseWidget):
	"""
	This class implements initial login control - Admin vs User
	"""

	def __init__(self):
		super(Login,self).__init__('Login')

		# Definition of form fields
		self._username	= ControlText('Username')
		self._password	= ControlText('Password')
		self._button	= ControlButton('Login')

		self.formset = ['_username','_password','_button',' ']

		self._button.value = self.__buttonAction

	def __buttonAction(self):
		self._username.value = self._password.value


if __name__ == "__main__":	pyforms.start_app( Login )
