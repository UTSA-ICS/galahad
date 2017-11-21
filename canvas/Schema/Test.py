from	__init__				import *
#from	TestDatabase			import TestDatabase

class Test:
	def __init__(self):
		pass

	# Admin
	# Imports a pre-defined User that will be used for testing. If called
	# multiple times for the same User, the same username should be
	# returned.
	# Return -> Credentials that can be used to log in as the user. Format
	# is implementation-specific.
	# Type -> object
	def importuser(self, userToken, which):
		return 254

	# Admin
	# Imports a pre-defined Application that will be used for testing. If
	# called multiple times for the same Application, the same ID should
	# be returned.
	# Return -> An ID that can be used for the indicated Application in
	# future calls. Format is implementation-specific.
	# Type -> String
	def importapplication(self, userToken, which):
		return 254

	# Admin
	# Imports a pre-defined Role that will be used for testing. If
	# called multiple times for the same Role, the same ID should be
	# returned.
	# Return -> An ID that can be used for the indicated Role in future
	# calls. Format is implementation-specific.
	# Type -> String
	def importrole(self, userToken, which):
		return 254
