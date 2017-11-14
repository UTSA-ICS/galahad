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

from	__init__				import *
from	VirtueDatabase			import VirtueDatabase

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
		virt = VirtueDatabase()
		virt.set_user(username)
		return virt.find_all()

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

	# Gets information about a specified Virtue by ID.
	# Type -> Virtue
	def get(self, userToken, virtId):
		virt = VirtueDatabase()
		return virt.find_one(virtId)

	# Creates a new Virtue with the given properties. Also enables any Transducers on the Virtue
	# that are supposed to be enabled on startup.
	# Type -> Virtue
	def create(self, userToken, roleId):
		virt = VirtueDatabase()
		# get username from UserToken - for now use 'kelli'
		virt.set_user('kelli')
		virt.set_state('CREATING')
		# virtue create app - set appId
		virt.set_values({
			'ROLEID'			: roleId,
			'RESOURCEIDS'		: 'resids',
			'TRANSDUCERIDS'		: 'transids',
		})
		return virt.find_one(virt.insert())

	# Launches a Virtue
	# Type -> Virtue
	def launch(self, userToken, virtId):
		return 254

	# Stops a running Virtue.
	# Type -> Virtue
	def stop(self, userToken, virtId):
		return 254

	# Destroys a Virtue. Releases all resources.
	# Exit code only
	def destroy(self, userToken, virtId):
		return 254

	# Launches an Application in a running Virtue.
	# Type -> object. Information about the launched Application. Format is implementation-specific.
	def applicationlaunch(self, userToken, virtId, appId):
		# return 254
		virt = self.get(userToken, virtId)
		# convert displayId to (virtId + '0' + id)[:10]
		app = json.loads(Application.get(Application(), userToken, appId))
		instr = "xpra attach ssh/" + str(virt['USERNAME'])			\
								   + "@" + str(virt['IPADDRESS'])	\
								   + "/" + str(virt['VIRTID'])
		thread.start_new_thread(self.launch_proc, (instr,))

	# Stops a running Application in the indicated Virtue.
	# Exit code only
	def applicationstop(self, userToken, virtId, appId):
		# return 254
		virt = self.get(userToken, virtId)
		instr = "xpra stop ssh/" + str(virt['USERNAME'])			\
								 + "@" + str(virt['IPADDRESS'])		\
								 + "/" + str(virt['VIRTID'])
		thread.start_new_thread(self.launch_proc, (instr,))

if __name__ == "__main__":
		virt = Virtue()
		print(virt.create('kelli','roleid'))
