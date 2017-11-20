import	dataset
import	json
import	time
import	datetime

from	__init__				import *
from	ApplicationDatabase		import ApplicationDatabase

class Application:
	APPID = ''		# Required - False		# Type -> String
	NAME = ''		# Required - True		# Type -> String
	VERSION = ''	# Required - True		# Type -> String
	OS = ''			# Required - True		# Type -> String (enum)
											#		  [LINUX, WINDOWS]

	def __init__(self):
		pass

	# Create new Application instance.
	# Type -> applicationId
	def create(self, userToken, name):
		app = ApplicationDatabase()
		app.set_user(userToken)
		app.set_values({
			'NAME'			: name,
			'OS'			: 'LINUX',		# determine here
		})
		return app.insert()



	"""
	API Defined
	"""

	# User
	# Gets information about the indicated application.
	# Type -> Application
	def get(self, userToken, applicationId):
		app = ApplicationDatabase()
		app.set_user(userToken)
		return app.find_one(applicationId)

	# Admin
	# Lists all applications currently available in the system.
	# Type -> list of Application
	def list(self, userToken):
		app = ApplicationDatabase()
		return app.find_all()

if __name__ == "__main__":
	app = Application()
	print app.list('kelli')
