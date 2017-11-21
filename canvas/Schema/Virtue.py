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

	# User
	# Gets information about a specified Virtue by ID.
	# Return -> Information about the indicated Virtue.
	# Type -> Virtue
	def get(self, userToken, virtId):
		virt = VirtueDatabase()
		return virt.find_one(virtId)

	# User
	# Creates a new Virtue with the given properties. Also enables any 
	# Transducers on the Virtue that are supposed to be enabled on startup.
	# Return -> Information about the created Virtue.
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

	# User
	# Launches a Virtue
	# Return -> Information about the launched Virtue.
	# Type -> Virtue
	def launch(self, userToken, virtId):
		return 254

	# User
	# Stops a running Virtue.
	# Return -> Information about the stopped Virtue.
	# Type -> Virtue
	def stop(self, userToken, virtId):
		return 254

	# User
	# Destroys a Virtue. Releases all resources.
	# Exit code only
	def destroy(self, userToken, virtId):
		return 254

	# User
	# Launches an Application in a running Virtue.
	# Return -> Information about the launched Application. Format is
	# implementation-specific.
	# Type -> object
	def applicationlaunch(self, userToken, virtId, appId):
		# return 254
		virt = self.get(userToken, virtId)
		# convert displayId to (virtId + '0' + id)[:10]
		app = json.loads(Application.get(Application(), userToken, appId))
		instr = "xpra attach ssh/" + str(virt['USERNAME'])			\
								   + "@" + str(virt['IPADDRESS'])	\
								   + "/" + str(virt['VIRTID'])
		thread.start_new_thread(self.launch_proc, (instr,))

	# User
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
