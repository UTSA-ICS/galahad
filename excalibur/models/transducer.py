from excalibur.ExcaliburException import *

import pymongo
from pymongo import MongoClient

client = pymongo.MongoClient()
collection = client.excalibur.transducers

class Transducer(object):

	def __init__(self, data):
		self.id = data.get('id', None)
		self.name = data.get('name', '')
		self.type = data.get('type', '')
		self.start_enabled = data.get('start_enabled', None)
		self.starting_configuration = data.get('starting_configuration', None)
		self.required_access = data.get('required_access', None)

	def __print(self, transducer):
		print 'ID:', transducer['id']
		print 'Name:', transducer['name']
		print 'Type:', transducer['type']
		print 'Start Enabled:', transducer['startEnabled']

	def list(self, userToken):
		'''
		Lists all transducers currently available in the system

		Args:
			userToken (UserToken): The UserToken for the logged-in admin user

		Returns:
			list: Transducer objects for known transducers
		'''

		all_transducers = []
		for transducer in collection.find():
			self.__print(transducer)
			all_transducers.append(Transducer(transducer))
		return all_transducers

	def get(self, userToken, transducerId):
		'''
		Gets information about the indicated Transducer. Does not include information about any
		instantiation in Virtues.

		Args:
			userToken (UserToken): The UserToken for the logged-in admin user
			transducerId (str): The ID of the Transducer to get.

		Returns:
			Transducer: information about the indicated transducer
		'''
		#raise NotImplemented("transducer.get")
		transducer = collection.find_one({ 'id': transducerId },{ '_id': 0 })
		if transducer is None:
			print 'No transducer found!'
			return None
		else:
			print self.__print(transducer)
			return Transducer(transducer)

	def enable(self, userToken, transducerId, virtueId, configuration):
		'''
		Enables the indicated Transducer in the indicated Virtue.

		Args:
			userToken (UserToken) : The UserToken for the logged-in admin user
			transducerId (str) : The ID of the Transducer to enable. 
			virtueId (str)     : The ID of the Virtue in which to enable the Transducer. 
			configuration (object): The configuration to apply to the Transducer when it is enabled. Format 
			                        is Transducer-specific. This overrides any existing configuration with the same keys.

		Returns:
			bool: True if the transducer was enabled, false otherwise

		'''
		raise NotImplemented("transducer.enable")

	def disable(self, userToken, transducerId, virtueId):
		'''
		Disables the indicated Transducer in the indicated Virtue

		Args:
			userToken (UserToken) : The UserToken for the logged-in admin user
			transducerId (str) : The ID of the Transducer to disable
			virtueId (str)     : The ID of the Virtue in which to enable the Transducer. 

		Returns:
			bool: True if the transducer was enabled, false otherwise
		'''
		raise NotImplemented("transducer.disable")

	def get_enabled(self, userToken, transducerId, virtueId):
		'''
		Gets the current enabled status for the indicated Transducer in the indicated Virtue.

		Args:
			userToken (UserToken) : The UserToken for the logged-in admin user
			transducerId (str) : The ID of the Transducer
			virtueId (str)     : The ID of the Virtue in which to enable the Transducer. 

		Returns:
			bool: True if the Transducer is enabled in the Virtue, false if it is not

		'''
		raise NotImplemented("transducer.get_enabled")

	def get_configuration(self, userToken, transducerId, virtueId):
		'''
		Gets the current configuration for the indicated Transducer in the indicated Virtue.

		Args:
			userToken (UserToken) : The UserToken for the logged-in admin user
			transducerId (str) : The ID of the Transducer
			virtueId (str)     : The ID of the Virtue in which to enable the Transducer. 

		Returns:
			TransducerConfig: Configuration information for the indicated Transducer in the indicated Virtue
		'''
		raise NotImplemented("transducer.get_configuration")

	def list_enabled(self, userToken, virtueId):
		'''
		Lists all Transducers currently that are currently enabled in the indicated Virtue.

		Args:
			userToken (UserToken) : The UserToken for the logged-in admin user
			virtueId (str)     : The ID of the Virtue in which to enable the Transducer. 

		Returns:
			list(Transducer): List of enabled transducers within the specified Virtue
		'''
		raise NotImplemented("transducer.list_enabled")


if __name__ == '__main__':
	
	data = {
			'id': 'test-transducer',
			'name': 'Test Transducer',
			'type': 'testing',
			'start_enabled': True,
			'starting_configuration': None,
			'required_access': []
	}

	t = Transducer(data)
	user_token = None

	try:
		t.get(user_token, None)
	except ExcaliburException as ee:
		print ee.retcode
		print ee
