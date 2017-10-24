import	dataset
import	json
import	time
import	datetime

from	Role					import Role

class Virtue:
	VIRTID = ''				# Required - False		# Type -> String
	USERNAME = ''			# Required - True		# Type -> String
	ROLEID = ''				# Required - True		# Type -> String
	APPLICATIONIDS = ''		# Required - True		# Type -> set of String
	RESOURCEIDS = ''		# Required - True		# Type -> set of String
	TRANSDUCERIDS = ''		# Required - True		# Type -> set of String
	STATE = ''				# Required - True		# Type -> String (enum)
													#		  [CREATING, STOPPED, LAUNCHING,
													#		   RUNNING, PAUSING, PAUSED,
													#		   RESUMING, STOPPING, DELETING]
	IPADDRESS = ''			# Required - False		# Type -> String (ip)


	def __init__(self):
		pass

	def getvirtuefromrole(self, userToken, roleId):
		db = dataset.connect('sqlite:///canvas.db')
		table = db['virtue']
		virt = table.find_one(ROLEID=roleId)
		return json.dumps(convertfromdb(virt))

	def converttostring(self, dlist):
		return ','.join(str(x) for x in dlist)

	def converttolist(self, string):
		return [str(x) for x in string.split(",")]

	def converttodb(self, d):
		return {
			'VIRTID'			: d['VIRTID'],
			'USERNAME'			: d['USERNAME'],
			'ROLEID'			: d['ROLEID'],
			'APPLICATIONIDS'	: self.converttostring(d['APPLICATIONIDS']),
			'RESOURCEIDS'		: self.converttostring(d['RESOURCEIDS']),
			'TRANSDUCERIDS'		: self.converttostring(d['TRANSDUCERIDS']),
			'STATE'				: d['STATE'],
			'IPADDRESS'			: d['IPADDRESS'],
		}

	def convertfromdb(self, d):
		return {
			'VIRTID'			: d['VIRTID'],
			'USERNAME'			: d['USERNAME'],
			'ROLEID'			: d['ROLEID'],
			'APPLICATIONIDS'	: self.converttolist(d['APPLICATIONIDS']),
			'RESOURCEIDS'		: self.converttolist(d['RESOURCEIDS']),
			'TRANSDUCERIDS'		: self.converttolist(d['TRANSDUCERIDS']),
			'STATE'				: d['STATE'],
			'IPADDRESS'			: d['IPADDRESS'],
		}


	"""
	API Defined
	"""

	def get(self, userToken, virtId):
		db = dataset.connect('sqlite:///canvas.db')
		table = db['virtue']
		virt = table.find_one(VIRTID=virtId)
		return json.dumps(virt)

	def create(self, userToken, roleId):
		db = dataset.connect('sqlite:///canvas.db')
		table = db['virtue']
		self.VIRTID 		= roleId + str(int(time.time()))
		self.USERNAME		= 'kelli'	# userToken.USERNAME
		self.ROLEID			= roleId
		self.APPLICATIONIDS = []
		self.RESOURCEIDS	= []
		self.TRANSDUCERIDS	= []
		self.STATE			= 'CREATING'
		self.IPADDRESS		= '10.20.20.180' # WILL BE AWS IP

		d = {
			'VIRTID'			: self.VIRTID,
			'USERNAME'			: self.USERNAME,
			'ROLEID'			: self.ROLEID,
			'APPLICATIONIDS'	: self.APPLICATIONIDS,
			'RESOURCEIDS'		: self.RESOURCEIDS,
			'TRANSDUCERIDS'		: self.TRANSDUCERIDS,
			'STATE'				: self.STATE,
			'IPADDRESS'			: self.IPADDRESS,
		}

		table.insert(self.converttodb(d))
		return json.dumps(d)

	def launch(self, userToken, virtId):
		return 254

	def stop(self, userToken, virtId):
		return 254

	def destroy(self, userToken, virtId):
		return 254

	def applicationlaunch(self, userToken, virtId, appId):
		return 254

	def applicationstop(self, userToken, virtId, appId):
		return 254


if __name__ == "__main__":
		role = Role()
		role.create('kelli', json.dumps(
			{
				'ROLEID'				: None,
				'NAME'					: 'Database Administrator',
				'VERSION'				: None,
				'APPLICATIONIDS'		: [],
				'STARTINGRESOURCEIDS'	: [],
				'STARTINGTRANSDUCERIDS'	: [],
			})
		)
		role.add('xterm')
		role.add('firefox')
		
		virtue = Virtue()
		print(role.get('kelli', role.ROLEID))
		print(virtue.create('kelli', role.ROLEID))
