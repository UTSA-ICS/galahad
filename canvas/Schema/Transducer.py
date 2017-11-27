from	__init__					import *
from	Virtue						import Virtue
from	TransducerDatabase			import TransducerDatabase

class Transducer:
	TRANSID = ''		# Required - False	# Type -> String
	NAME = ''			# Required - True	# Type -> String
	TYPE = ''			# Required - True	# Type -> String (enum)
											#		  [SENSOR, ACTUATOR]
	STARTENABLED = ''	# Required - True	# Type -> Boolean
	STARTCONFIG = ''	# Required - True	# Type -> object
	REQACCESS = ''		# Required - False	# Type -> set of Strings (enum)
											#		  [NETWORK, DISK,
											#		   MEMORY]
	"""
	Currently using local databases for testing until the REST server
	is functional. <- In Progress
	"""


	def __init__(self):
		pass

	# Security
	# Lists all Transducers currently available in the system.
	# Return -> All the Transducers, with IDs.
	# Type -> list of Transducer
	def list(self, userToken):
		# return 254
		transducer = TransducerDatabase()
		transducer.set_user(userToken)
		return transducer.find_all()

	# Security
	# Gets information about the indicated Transducer. Does not include
	# information about any instantiation in Virtues.
	# Return -> Information about the indicated Transducer.
	# Type -> Transducer
	def get(self, userToken, transducerId):
		#return 254
		transducer = TransducerDatabase()
		transducer.set_user(userToken)
		return transducer.find_one(transducerId)

	# Security
	# Enables the indicated Transducer in the indicated Virtue.
	# Error code only
	def enable(self, userToken, transducerId, virtueId, configuration):
		#return 254
		transducer = self.get(userToken, transducerId)
		virtue = Virtue().get(userToken, virtueId)
		print (str(virtue['TRANSDUCERIDS']) + ',' + transducerId)

	# Security
	# Disables the indicated Transducer in the indicated Virtue.
	# Error code only
	def disable(self, userToken, transducerId, virtueId):
		return 254

	# Security
	# Gets the current enabled status for the indicated Transducer in the
	# indicated Virtue.
	# Return -> Whether the indicated Transducer in the indicated Virtue
	# is enabled (true) or disabled (false).
	# Type -> Boolean
	def getenabled(self, userToken, transducerId, virtueId):
		return 254

	# Security
	# Gets the current configuration for the indicated Transducer in the
	# indicated Virtue.
	# Return -> Configuration information for the indicated Transducer in
	# the indicated Virtue. Format is Transducer-specific.
	# Type -> object
	def getconfiguration(self, userToken, transducerId, virtueId):
		return 254

	# Security
	# Lists all Transducers that are currently enabled in the indicated
	# Virtue.
	# Return -> All the Transducers, with IDs.
	# Type -> list of Transducer
	def listenabled(self, userToken, virtueId):
		return 254

if __name__ == '__main__':
	transducer = Transducer()
	virtue = Virtue().create('kelli', 'roleid')
	transducer.enable('kelli', 'temp', virtue['VIRTID'], '')
