import 	pyforms
from	pyforms				import BaseWidget
from	pyforms.Controls	import ControlText
from	pyforms.Controls	import ControlButton

class SimpleExample1(BaseWidget):
	def __init__(self):
		super(SimpleExample1,self).__init__('Simple example 1')

		# Definition of the forms fields
		self._firstname		= ControlText('First name', 'Default value')
		self._middlename	= ControlText('Middle name')
		self._lastname		= ControlText('Lastname name')
		self._fullname		= ControlText('Full name')
		self._button		= ControlButton('Press this button')

		# Define the button action
		self._button.value = self.__buttonAction

		# Define the organization of the forms
		#self.formset = [ ('_firstname','_middlename','_lastname'), '_button', '_fullname', ' ']
		# The ' ' is used to indicate that an empty space should be placed at the bottom of the window
		# If you remove the ' ' the forms will occupy the entire window

		self.formset = [ {
			'Tab1':['_firstname','||','_middlename','||','_lastname'],
			'Tab2':['_fullname']
			},
			'=',(' ','_button',' ')]
		# Use dictionaries for tabs
		# Use the sign '=' for a vertical splitter
		# Use the signs '||' for a horizontal splitter

	def __buttonAction(self):
		"""Button action event"""
		self._fullname.value = self._firstname.value +" "+ self._middlename.value +" "+ self._lastname.value

# Execute the application
if __name__ == "__main__":	pyforms.start_app( SimpleExample1 )
