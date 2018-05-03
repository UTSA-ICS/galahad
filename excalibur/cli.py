#!/usr/bin/env python

import configparser
import cmd
import gnureadline as readline
import os.path
import sys
import traceback

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

		# Read config file if exists
		if os.path.isfile(dotfile):
			config = configparser.ConfigParser()
			config.read(dotfile)
			Transducer({}).set_api_config(userToken, config)

	def do_enable(self, args):
		'''Enable a transducer by (transducer_id, virtue_id) with configuration'''
		args_tok = args.split(' ')
		if not len(args_tok) == 3:
			raise InvalidOrMissingParameters(details='Usage: transducer enable [transducer_id] [virtue_id] [configuration]')
		trans_id, virtue_id, configuration = args_tok

		ret = Transducer({}).enable(self.user_token, trans_id, virtue_id, configuration)
		if ret:
			print 'Success'
		else:
			print 'Failure or delayed ACK'
		return ret

	def do_disable(self, args):
		'''Disable a transducer by (transducer_id, virtue_id)'''
		args_tok = args.split(' ')
		if not len(args_tok) == 2:
			raise InvalidOrMissingParameters(details='Usage: transducer disable [transducer_id] [virtue_id]')
		trans_id, virtue_id = args_tok

		ret = Transducer({}).disable(self.user_token, trans_id, virtue_id)
		if ret:
			print 'Success'
		else:
			print 'Failure or delayed ACK'
		return ret

	def do_get(self, args):
		'''Retrieve information about a transducer by transducer_id'''
		if not len(args.split(' ')) == 1:
			raise InvalidOrMissingParameters(details='Usage: transducer get [transducer_id]')
		trans_id = args

		info = Transducer({}).get(self.user_token, trans_id)
		print info
		return info

	def do_get_configuration(self, args):
		'''Retrieve a transducer configuration by (transducer_id, virtue_id)'''
		args_tok = args.split(' ')
		if not len(args_tok) == 2:
			raise InvalidOrMissingParameters(details='Usage: transducer get configuration [transducer_id] [virtue_id]')
		transducer_id, virtue_id = args_tok

		config = Transducer({}).get_configuration(self.user_token, transducer_id, virtue_id)
		print config
		return config

	def do_get_enabled(self, args):
		'''Retrieve current enabled state for a specified (transducer_id, virtue_id)'''
		args_tok = args.split(' ')
		if not len(args_tok) == 2:
			raise InvalidOrMissingParameters(details='Usage: transducer get_enabled [transducer_id] [virtue_id]')

		transducer_id = args_tok[0]
		virtue_id = args_tok[1]

		enabled = Transducer({}).get_enabled(self.user_token, transducer_id, virtue_id)
		print enabled
		return enabled

	def do_list(self, args):
		'''List all transducers available in the system'''
		if args != '':
			raise InvalidOrMissingParameters(details='Usage: transducer list')

		all_transducers = Transducer({}).list(self.user_token)
		print all_transducers
		return all_transducers

	def do_list_enabled(self, virtue_id):
		'''List all enabled transducers'''
		if virtue_id == '':
			raise InvalidOrMissingParameters(details='Usage: transducer list_enabled [virtue_id]')

		enabled = Transducer({}).list_enabled(self.user_token, virtue_id)
		print enabled
		return enabled

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
			print e
			if verbose:
				traceback.print_exc()


if __name__ == '__main__':
	import sys
	if len(sys.argv) > 1:
		ExcaliburCmd().onecmd(' '.join(sys.argv[1:]))
	else:
		try:
			ExcaliburCmd().cmdloop(banner)
		except KeyboardInterrupt:
			print "Goodbye!"
