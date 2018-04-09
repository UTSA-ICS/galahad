import pymongo
from pymongo import MongoClient

client = pymongo.MongoClient()
collection = client.excalibur.virtues

class Virtue(object):

	def __init__(self, data):
		self.id = data.get('id', None)
		self.username = data.get('name', '')
		self.role_id = data.get('role_id', '')
		self.application_ids = data.get('application_ids', None)
		self.resource_ids = data.get('resource_ids', None)
		self.transducer_ids = data.get('transducer_ids', None)
		self.state = data.get('state', '')
		self.ip_address = data.get('ip_address', '')

	# Gets information about a specified Virtue by ID.
	def get(self):
		return 254

	# Creates a new Virtue with the given properties. Also enables any Transducers on the Virtue that are supposed to be enabled on startup.
	def create(self):
		return 254

	# Launches a Virtue.
	def launch(self):
		return 254

	# Stops a running Virtue.
	def stop(self):
		return 254

	# Destroys a Virtue. Releases all resources.
	def destroy(self):
		return 254

	# Launches an Application in a running Virtue.
	def application_launch(self):
		return 254

	# Stops a running Application in the indicated Virtue.
	def application_stop(self):
		return 254
