import	dataset

class UserToken:
	USERNAME = None			# Required - True		# Type -> String
	TOKEN = None			# Required - True		# Type -> String (uuid)
	EXPIRATION = None		# Required - True		# Type -> String (date - time)


	def __init__(self):
		pass

	def list(self):
		return 254

	# TEMPORARY FOR TESTING ONLY
	def create(self):
		db = dataset.connect('sqlite:///canvas.db')
		table = db['userToken']
		d = {
			'USERNAME'		:	'kelli',
			'TOKEN'			:	'kelli',
			'EXPIRATION'	:	'never',
		}
		table.insert(d)

	def getusername(self,token):
		db = dataset.connect('sqlite:////home/kelli/galahad/canvas/Schema/canvas.db')
		table = db['userToken']
		userToken = table.find_one(TOKEN=token)
		return userToken['USERNAME']

if __name__ == "__main__":
		ut = UserToken()
		ut.create()
		print(ut.getusername('kelli'))
