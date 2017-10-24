from	PyQt5		import QtGui

class AddMenuFunctionality(object):
	"""
	This class is a module of the application PeopleWindow.py
	It is a simple example of how apps can be divided in modules with pyforms
	It adds the Open and Save functionality
	"""

	def __init__(self):
		# It adds the next options to the main menu
		self.mainmenu.append(
			{ 'File': [
				{'Save as': self.__savePeople},
				{'Open as': self.__loadPeople},
				'-',
				{'Exit': self.__exit},
			] }
		)

	def __savePeople(self):
		filename = QtGui.QFileDialog.getSaveFileName(parent=self,
			caption="Save file",
			directory=".",
			filter="*.dat")

		if filename!=None and filename!='': self.save(filename)

	def __loadPeople(self):
		filename = QtGui.QFileDialog.getOpenFileName(parent=self,
			caption="Import file",
			directory=".",
			filter="*.dat")

		if filename!=None and filename!='':
			self.load(filename)
			for person in self.__people:
				self._peopleList += [person._firstName, person._middleName, person._lastName]

	def __exit(self):
		exit()
