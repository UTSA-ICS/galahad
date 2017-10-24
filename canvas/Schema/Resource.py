import	dataset
import	json

class Resource:
	RESID = ''			# Required - False		# Type -> String
	TYPE = ''			# Required - True		# Type -> String (enum)
	UAC = ''			# Required - True		# Type -> Universal Naming Convention
	CREDENTIALS = ''	# Required - False		# Type -> Object


	def __init__(self):
		pass

	def save(self):
		db = dataset.connect('sqlite:///canvas.db')
		table = db['resource']
		d = {
			'RESID'			:	self.RESID,
			'TYPE'			:	self.TYPE,
			'UAC'			:	self.UAC,
			'CREDENTIALS'	:	self.CREDENTIALS,
		}
		table.insert(d)
		return 0

	def get(self, userToken, resid):
		db = dataset.connect('sqlite:///canvas.db')
		table = db['resource']
		res = table.find_one(RESID=resid)
		return json.dumps(res)

	def list(self, userToken):
		ress = []
		db = dataset.connect('sqlite:///canvas.db')
		result = db['resource'].all()
		for res in result:
			ress.append(json.dumps(res))
		return ress

	def attach(self, userToken, resId, virtId):
		return 254

	def detach(self, userToken, resId, virtId):
		return 254
