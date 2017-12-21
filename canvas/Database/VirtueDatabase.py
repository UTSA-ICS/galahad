import	dataset
import	time
import	datetime
import	uuid, re

class VirtueDatabase:
	def __init__(self):
		self._virtueId = None
		self._username = None
		self._roleId = None
		self._applicationIds = None
		self._resourceIds = None
		self._transducerIds = None
		self._state = None
		self._ipaddress = None
		self._db = dataset.connect('sqlite:////home/kelli/galahad/canvas/Database/canvas.db')
		self._table = self._db['VIRTUE']

	def set_user(self, username):
		self._username = username

	# poll AWS - for now = 'kelli-test-xpra2'
	def set_state(self, state):
		self._state = state

	def set_ip(self, ipaddress):
		self._ipaddress = ipaddress

	def set_appid(self, appId):
		self._applicationIds = appId

	def set_values(self, values_json):
		self._roleId = values_json['ROLEID']
		self._resourceIds = values_json['RESOURCEIDS']
		self._transducerIds = values_json['TRANSDUCERIDS']
		
		if self._virtueId == None:	
			self._virtueId = re.sub("[^0-9]","",str(uuid.uuid4()))
		# for testing purposes
		if self._ipaddress == None:
			self._ipaddress = 'kelli-test-xpra2'

	def insert(self):
		d = {
			'VIRTID'				: self._virtueId,
			'USERNAME'				: self._username,
			'ROLEID'				: self._roleId,
			'APPLICATIONIDS'		: self._applicationIds,
			'RESOURCEIDS'			: self._resourceIds,
			'TRANSDUCERIDS'			: self._transducerIds,
			'STATE'					: self._state,
			'IPADDRESS'				: self._ipaddress,
		}
		self._table.upsert(d, ['VIRTID'])
		return self._virtueId

	def find_one(self, virtueId):
		return self._table.find_one(VIRTID=virtueId)

	def find_all(self):
		virts = []
		for virt in self._table.find(USERNAME=self._username):
			virts.append(virt)
		return virts

if __name__ == "__main__":
	virt = VirtueDatabase()
	virt.set_user('kelli')
	virt.set_state('CREATING')
	virt.set_ip('kelli-test-xpra2')
	virt.set_values({'ROLEID':'roleid','RESOURCEIDS':'resid','TRANSDUCERIDS':'("1","2")'})
	virtId = virt.insert()
	#print virt.find_one(virtId)

	virt.set_state('PAUSED')
	virt.set_appid('appid')
	virtId = virt.insert()
	setof = virt.find_one(virtId)['TRANSDUCERIDS']
	print setof
	print [str(x) for x in setof.split(",")]
