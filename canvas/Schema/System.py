from	 __init__				import *
#from	SystemDatabase			import SystemDatabase

class System:
	def __init__(self):
		pass

	# Admin
	# Export the Virtue system to a file.
	# Return -> Exported Virtue system in the bytestream format.
	# Type -> bytes
	def export(self, userToken):
		return 254

	# Admin
	# Import the Virtue system from the input bytestream data.
	# Error code only.
	def import(self, userToken, data):
		return 254
