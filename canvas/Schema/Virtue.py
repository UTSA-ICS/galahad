import	dataset
import	json
import	time
import	datetime

import	thread
import	time
import	shlex
from	subprocess				import Popen, PIPE

from	Role					import Role
from	Application				import Application

class Virtue:
	VIRTID = ''				# Required - False		# Type -> String
	USERNAME = ''			# Required - True		# Type -> String
	ROLEID = ''				# Required - True		# Type -> String
	APPLICATIONIDS = []		# Required - True		# Type -> set of String
	RESOURCEIDS = []		# Required - True		# Type -> set of String
	TRANSDUCERIDS = []		# Required - True		# Type -> set of String
	STATE = ''				# Required - True		# Type -> String (enum)
													#		  [CREATING, STOPPED, LAUNCHING,
													#		   RUNNING, PAUSING, PAUSED,
													#		   RESUMING, STOPPING, DELETING]
	IPADDRESS = ''			# Required - False		# Type -> String (ip)


	def __init__(self):
		pass

	# MULTITHREADING FUNCTION FOR PROCESS LAUNCH WITHIN VIRTUE INSTANCE
	def launch_proc(self, instr):
		print(instr)
		args = shlex.split(instr)
		p = Popen(args, shell=False, stdout=PIPE, stdin=PIPE)
		return 0

	def getvirtuesfromuser(self, username):
		db = dataset.connect('sqlite:////home/kelli/galahad/canvas/Schema/canvas.db')
		table = db['virtue']
		virts = table.find(USERNAME=username)
		virtlist = []
		for virt in virts:
			virtlist.append(virt)
		return virtlist

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

	# UPDATE RESOURCEIDS LIST IN GIVEN VIRTUE
	def updateres(self, userToken, reslist, virt):
		# return 254
		db = dataset.connect('sqlite:///canvas.db')
		table = db['virtue']	
		table.update({
			'VIRTID'			: virt['VIRTID'],
			'RESOURCEIDS'		: reslist
		}, ['VIRTID'])

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
		self.VIRTID 		= str(int(time.time()))[-4:]
		self.USERNAME		= 'kelli'	# userToken.USERNAME
		self.ROLEID			= roleId
		self.APPLICATIONIDS = []
		self.RESOURCEIDS	= []
		self.TRANSDUCERIDS	= []
		self.STATE			= 'CREATING'
		self.IPADDRESS		= '10.20.20.179' # WILL BE AWS IP

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
		# return 254
		virt = json.loads(self.get(userToken, virtId))
		app = json.loads(Application.get(Application(), userToken, appId))
		instr = "xpra attach ssh/" + str(virt['USERNAME'])			\
								   + "@" + str(virt['IPADDRESS'])	\
								   + "/" + str(virt['VIRTID'])
		thread.start_new_thread(self.launch_proc, (instr,))

	def applicationstop(self, userToken, virtId, appId):
		# return 254
		virt = json.loads(self.get(userToken, virtId))
		instr = "xpra stop ssh/" + str(virt['USERNAME'])			\
								 + "@" + str(virt['IPADDRESS'])		\
								 + "/" + str(virt['VIRTID'])
		thread.start_new_thread(self.launch_proc, (instr,))

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

		app = Application()
		virtue = Virtue()
		print(app.create('xterm'))
		print(app.NAME)
		virtue.create('kelli', str(2))
		virtue.applicationlaunch('kelli', virtue.VIRTID, app.APPID)
		time.sleep(15)
		virtue.applicationstop('kelli', virtue.VIRTID, app.APPID)
		time.sleep(5)
