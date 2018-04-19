#!/usr/bin/env python

import configparser
import cmd
import gnureadline as readline
import json
import os.path
import rethinkdb as r
import sys
import traceback
import time
from copy import deepcopy
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA

from ExcaliburException import *
from models.transducer import Transducer

# Note that the backslashes are escaped 
banner = '''            /<        _____              _ _ _                
           /<        |  ___|            | (_) |               
 |\_______{o}--------| |____  _____ __ _| |_| |__  _   _ _ __------------_
[\\\\\\\\\\\\\\\\\\\\\{*}:::<==|  __\\ \\/ / __/ _` | | | '_ \\| | | | '__|======---   >
 |/~~~~~~~{o}--------| |___>  < (_| (_| | | | |_) | |_| | |  ------------~
           \\<        \\____/_/\\_\\___\\__,_|_|_|_.__/ \\__,_|_|   
            \\<'''

verbose = False

dotfile = '.excalibur'

def str2bool(v):
	return v.lower() in ("yes", "true", "t", "1", "y")

class TransducerCmd(cmd.Cmd):

	def __init__(self, userToken):
		cmd.Cmd.__init__(self)
		self.user_token = userToken

		# Default values
		self.rethinkdb_host = 'ec2-54-145-211-31.compute-1.amazonaws.com'
		self.ca_cert = 'rethinkdb_cert.pem'
		self.excalibur_key_file = 'excalibur_key.pem'
		self.virtue_key_dir = '.'

		# Read config file if exists
		if os.path.isfile(dotfile):
			config = configparser.ConfigParser()
			config.read(dotfile)
			if 'transducer' in config:
				if 'rethinkdb_host' in config['transducer']:
					self.rethinkdb_host = config['transducer']['rethinkdb_host']
				if 'rethinkdb_ca_cert' in config['transducer']:
					self.ca_cert = config['transducer']['rethinkdb_ca_cert']
				if 'excalibur_private_key' in config['transducer']:
					self.excalibur_key_file = config['transducer']['excalibur_private_key']
				if 'virtue_public_key_dir' in config['transducer']:
					self.virtue_key_dir = config['transducer']['virtue_public_key_dir']

		# Check that files exist
		if not os.path.isfile(self.ca_cert):
			print 'ERROR: File not found for RethinkDB CA cert:', self.ca_cert
			raise InvalidOrMissingParameters()
		if not os.path.isfile(self.excalibur_key_file):
			print 'ERROR: File not found for Excalibur private key:', self.excalibur_key_file
			raise InvalidOrMissingParameters()
		if not os.path.isdir(self.virtue_key_dir):
			print 'ERROR: Directory not found for Virtue public keys:', self.virtue_key_dir
			raise InvalidOrMissingParameters()

		# RethinkDB connection
		with open(self.excalibur_key_file, 'r') as f:
			key = f.read()
			self.excalibur_key = RSA.importKey(key)
			try:
				self.conn = r.connect(host=self.rethinkdb_host, 
					user='excalibur', 
					password=key, 
					ssl={ 'ca_certs': self.ca_cert })
			except r.ReqlDriverError as e:
				print 'ERROR: Failed to connect to RethinkDB at host:', self.rethinkdb_host, 'error:', e
				return

		# Make sure that the database and tables have been set up
		# NOTE: This doesn't set the permissions for the users.  That is only done by the setup_rethinkdb.py script - please run that before running the Excalibur CLI!!!
		try:
			r.db_create('transducers').run(self.conn)
		except r.ReqlOpFailedError:
			# database already exists - great
			pass

		try:
			r.db('transducers').table_create('commands').run(self.conn)
		except r.ReqlOpFailedError:
			# table already exists - great
			pass

		try:
			r.db('transducers').table_create('acks').run(self.conn)
		except r.ReqlOpFailedError:
			# table already exists - great
			pass

	def do_enable(self, args):
		'''Enable a transducer by (transducer_id, virtue_id) with configuration'''
		args_tok = args.split(' ')
		if not len(args_tok) == 3:
			raise InvalidOrMissingParameters()
		trans_id, virtue_id, configuration = args_tok
		print "transducer.enable(" + ", ".join(args_tok) + ")"

		if self.__change_ruleset(virtue_id, trans_id, True, config=configuration):
			print 'Success'
			return True
		else:
			print 'Failure'
			return False

	def do_disable(self, args):
		'''Disable a transducer by (transducer_id, virtue_id)'''
		args_tok = args.split(' ')
		if not len(args_tok) == 2:
			raise InvalidOrMissingParameters()
		trans_id, virtue_id = args_tok
		print "transducer.disable(" + ", ".join(args_tok) + ")"

		if self.__change_ruleset(virtue_id, trans_id, False):
			print 'Success'
			return True
		else:
			print 'Failure'
			return False

	def __sign_message(self, row):
		required_keys = ['virtue_id', 'transducer_id', 'configuration', 
			'enabled', 'timestamp']
		if not all( [ (key in row) for key in required_keys ] ):
			print 'ERROR: Missing required keys in row:',\
				filter((lambda key: key not in row), required_keys)
			return None

		message = '|'.join([row['virtue_id'], row['transducer_id'], 
			str(row['configuration']), str(row['enabled']), str(row['timestamp'])])
		h = SHA.new(str(message))
		signer = PKCS1_v1_5.new(self.excalibur_key)
		signature = signer.sign(h)
		return signature

	def __verify_message(self, row):
		if row is None:
			print 'ERROR: No match found'
			return False

		required_keys = ['virtue_id', 'transducer_id', 'configuration', 
			'enabled', 'timestamp', 'signature']
		if not all( [ (key in row) for key in required_keys ] ):
			print 'ERROR: Missing required keys in row:',\
				filter((lambda key: key not in row),required_keys)
			return False

		message = '|'.join([row['virtue_id'], row['transducer_id'], 
			str(row['configuration']), str(row['enabled']), str(row['timestamp'])])

		virtue_public_key = os.path.join(self.virtue_key_dir, 
			'virtue_' + row['virtue_id'] + '_pub.pem')
		if not os.path.isfile(virtue_public_key):
			print 'ERROR: No file found for Virtue public key at:',\
				virtue_public_key
			return False
		with open(virtue_public_key) as f:
			virtue_key = RSA.importKey(f.read())

		h = SHA.new(str(message))
		verifier = PKCS1_v1_5.new(virtue_key)
		verified = verifier.verify(h, row['signature'])
		if not verified:
			printable_msg = copy.deepcopy(row)
			del printable_msg['signature']
			print 'ERROR: Unable to validate signature of ACK message:',\
				json.dumps(printable_msg, indent=2)
		return verified

	def __change_ruleset(self, virtue_id, trans_id, enable, config=None):
		timestamp = int(time.time())

		row = {
			'id': [virtue_id, trans_id],
			'virtue_id': virtue_id,
			'transducer_id': trans_id,
			'configuration': config,
			'enabled': enable,
			'timestamp': timestamp
		}
		signature = self.__sign_message(row)
		row['signature'] = r.binary(signature)

		# Send command to change ruleset
		try:
			res = r.db('transducers').table('commands')\
				.insert(row, conflict='replace').run(self.conn)
			if res['errors'] > 0:
				print 'ERROR: Failed to insert into commands table; first error:'
				print res['first_error']
				return False
		except r.ReqlError as e:
			print 'ERROR: Failed to insert into commands table because:', e
			return False

		# Wait for ACK from the virtue that the ruleset has been changed
		#try:
		cursor = r.db('transducers').table('acks')\
			.get([virtue_id, trans_id])\
			.changes(squash=False).run(self.conn)
		#except r.ReqlError as e:
		#	print 'ERROR: Failed to read from the ACKs table because:', e
		#	return False

		retry = True
		while retry:
			try:
				retry = False
				# Wait max 30 seconds - if we miss the real ACK, hopefully
				# at least the next heartbeat will suffice
				print 'INFO: Waiting for ACK'
				change = cursor.next(wait=30)
				row = change['new_val']
				verified = self.__verify_message(row)
				if verified:
					if row['timestamp'] >= timestamp:
						if row['enabled'] == enable:
							print 'INFO: ACK received!'
							return True
						else:
							print 'ERROR: Enable incorrect:', enable, row['enabled']
							return False
					else:
						print 'WARN: Timestamp incorrect:', timestamp, row['timestamp']
						# Retry once in case that was just a wayward ACK
						retry = True
				else:
					print 'ERROR: Received invalid ACK'
			except (r.ReqlCursorEmpty, r.ReqlDriverError) as e:
				print 'ERROR: Failed to receive ACK before timeout'
				return False
			finally:
				cursor.close()
		return False

	def do_get(self, args):
		'''Retrieve information about a transducer by transducer_id'''
		if not len(args.split(' ')) == 1:
			raise InvalidOrMissingParameters()
		trans_id = args
		print "transducer.get(" + args + ")"

		return Transducer({}).get(self.user_token, trans_id)

	def do_get_configuration(self, args):
		'''Retrieve a transducer configuration by (transducer_id, virtue_id)'''
		args_tok = args.split(' ')
		if not len(args_tok) == 2:
			raise InvalidOrMissingParameters()
		transducer_id, virtue_id = args_tok
		print "transducer.get_configuration(" + ", ".join([transducer_id, virtue_id]) + ")"

		try:
			row = r.db('transducers').table('acks')\
				.get([virtue_id, transducer_id]).run(self.conn)
		except r.ReqlError as e:
			print 'ERROR: Failed to get info about transducer because:', e

		verified = self.__verify_message(row)
		if verified:
			# Message signature matches
			print row['configuration']
			return row['configuration']
		else:
			print 'ERROR: Information fails signature validation'
			return None

	def do_get_enabled(self, args):
		'''Retrieve current enabled state for a specified (transducer_id, virtue_id)'''
		args_tok = args.split(' ')
		if not len(args_tok) == 2:
			raise InvalidOrMissingParameters()
		print "transducer.get_enabled(" + ", ".join(args_tok) + ")"

		transducer_id = args_tok[0]
		virtue_id = args_tok[1]

		try:
			row = r.db('transducers').table('acks')\
				.get([virtue_id, transducer_id]).run(self.conn)
		except r.ReqlError as e:
			print 'ERROR: Failed to get info about transducer because:', e

		verified = self.__verify_message(row)
		if verified:
			# Message signature matches
			print row['enabled']
			return row['enabled']
		else:
			print 'ERROR: Information fails signature validation'
			return None

	def do_list(self, line):
		'''List all transducers available in the system'''
		print "transducer.list()"

		return Transducer({}).list(self.user_token)

	def do_list_enabled(self, virtue_id):
		'''List all enabled transducers'''
		print "transducer.list_enabled(" + virtue_id + ")"

		enabled_transducers = []

		try:
			for row in r.db('transducers').table('acks')\
				.filter( { 'virtue_id': virtue_id } ).run(self.conn):

				verified = self.__verify_message(row)
				if verified:
					if ('enabled' in row) and row['enabled']:
						print row['transducer_id']
						enabled_transducers.append(row['transducer_id'])
				else:
					print 'ERROR: Info about transducer',\
						row['transducer_id'],\
						'fails signature validation'

		except r.ReqlError as e:
			print 'ERROR: Failed to get enabled transducers because:', e

		return enabled_transducers

class ExcaliburCmd(cmd.Cmd):

	def __init__(self):
		cmd.Cmd.__init__(self)
		self.prompt = "==> "
		self.intro = banner

	def preloop(self):
		"""Initialization before prompting user for commands.
		   Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
		"""
		cmd.Cmd.preloop(self)   ## sets up command completion
		self._hist    = []      ## No history yet
		self._locals  = {}      ## Initialize execution namespace for user
		self._globals = {}

		# Need to add a pre-hook to figure out the user token stuff

	def postloop(self):
		"""Take care of any unfinished business.
		   Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
		"""

		# Invalidate user token

		cmd.Cmd.postloop(self)   ## Clean up command completion
		print "Exiting..."

	def do_exit(self, line):
		print "Goodbye!"
		sys.exit(0)

	def do_EOF(self, line):
		print "Goodbye!"
		return True

	def do_verbose(self, arg):
		'''Set or get the current verbose/not verbose setting'''
		global verbose
		if arg == '':
			print "Verbose currently is", verbose
		elif str2bool(arg):
			print "*** Setting verbose=True"
			lverbose = True
		else:
			print "*** Setting verbose=False"
			verbose = False

	def do_help(self, args):
		'''Get help on commands
		   'help' or '?' with no arguments prints a list of commands for which help is available
		   'help <command>' or '? <command>' gives help on <command>
		'''
		## The only reason to define this method is for the help text in the doc string
		cmd.Cmd.do_help(self, args)

	def do_transducer(self, subcmd):
		'''Interact with the transducer subsystem. Valid commands:
	list
	list_enabled
	get_configuration
		'''
		try:
			TransducerCmd("MAH-TOKEN").onecmd(subcmd)
		except ExcaliburException as ee:
			print "ERROR: return code =", ee.retcode
			if verbose:
				traceback.print_exc()
			raise ee


if __name__ == '__main__':
	import sys
	if len(sys.argv) > 1:
		ExcaliburCmd().onecmd(' '.join(sys.argv[1:]))
	else:
		try:
			ExcaliburCmd().cmdloop(banner)
		except InvalidOrMissingParameters:
			print 'Invalid or missing paramenters.  Try again.'
		except KeyboardInterrupt:
			print "Goodbye!"
