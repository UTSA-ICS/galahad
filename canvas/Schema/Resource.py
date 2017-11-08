import	dataset
import	json

from	Virtue				import Virtue

class Resource:
	RESID = ''			# Required - False		# Type -> String
	TYPE = ''			# Required - True		# Type -> String (enum)
	UAC = ''			# Required - True		# Type -> Universal Naming Convention
	CREDENTIALS = ''	# Required - False		# Type -> Object


	def __init__(self):
		pass

	def converttostring(self, dlist):
		return ','.join(str(x) for x in dlist)

	def converttolist(self, string):
		return [str(x) for x in string.split(",")]

	# need create function
	
	"""
	API Defined
	"""

	# GET FUNCTION - RETURNS FULL RESOURCE OBJECT FROM RESID
	def get(self, userToken, resid):
		db = dataset.connect('sqlite:///canvas.db')
		table = db['resource']
		res = table.find_one(RESID=resid)
		return json.dumps(res)

	# LIST ALL RESOURCE OBJECTS AVAILABLE TO A USER
	def list(self, userToken):
		ress = []
		db = dataset.connect('sqlite:///canvas.db')
		result = db['resource'].all()
		for res in result:
			ress.append(json.dumps(res))
		return ress

	# ADD CREATED RESOURCE WITH RESID TO APPROPRIATE VIRTUE WITH VIRTID
	def attach(self, userToken, resId, virtId):
		# return 254
		virt = json.loads(Virtue.get(Virtue(), userToken, virtId))
		reslist = self.converttolist(virt['RESOURCEIDS'])
		reslist.append(resId)
		Virtue.updateres(Virtue(), userToken, self.converttostring(reslist), virt)

	# REMOVE AS ABOVE
	def detach(self, userToken, resId, virtId):
		# return 254
		virt = json.loads(Virtue.get(Virtue(), userToken, virtId))
		reslist = self.converttolist(virt['RESOURCEIDS'])
		reslist.remove(resId)
		Virtue.updateres(Virtue(), userToken, self.converttostring(reslist), virt)


if __name__ == '__main__':
		virt = Virtue()
		virt.create('kelli', 2)
	
		res = Resource()
		res.attach('kelli', str(3), virt.VIRTID)
		print(virt.get('kelli', virt.VIRTID))
		res.detach('kelli', str(3), virt.VIRTID)
		print(virt.get('kelli', virt.VIRTID))
