#!/usr/bin/env python

# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

import configparser
import cmd
import gnureadline as readline
import json
import os.path
import sys
import traceback

from apiendpoint import EndPoint
from apiendpoint_admin import EndPoint_Admin
from apiendpoint_security import EndPoint_Security

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


class ExcaliburCmd(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "==> "
        self.intro = banner

        self.username = None
        self.password = None

    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        cmd.Cmd.preloop(self)  ## sets up command completion
        self._hist = []  ## No history yet
        self._locals = {}  ## Initialize execution namespace for user
        self._globals = {}

        # Need to add a pre-hook to figure out the user token stuff

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """

        # Invalidate user token

        cmd.Cmd.postloop(self)  ## Clean up command completion
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

    def do_login(self, args):
        arg_tok = args.split(' ')
        if len(arg_tok) != 2:
            print 'Usage: login username password'
            return

        self.username = arg_tok[0]
        self.password = arg_tok[1]

    def default(self, line):
        if line == '':
            return

        if self.username is None or self.password is None:
            print 'Please log in first: login [username] [password]'
            return

        lineargs = line.split(' ')
        method = lineargs[0]
        args = lineargs[1:]

        ep_user = EndPoint(self.username, self.password)
        ep_admin = EndPoint_Admin(self.username, self.password)

        # Figure out what API the method is in and call the method with the rest of the args
        # NOTE that this doesn't check your syntax nor provide hints on what the syntax is
        if method.startswith('transducer_'):
            # Security API (transducer)
            ep = EndPoint_Security(self.username, self.password)

            # Read config file if exists
            if os.path.isfile(dotfile):
                config = configparser.ConfigParser()
                config.read(dotfile)
                ep.set_api_config(config)

            # Get the acutal method, and call it (with extra args)
            method_call = getattr(ep, method)
            if method_call is None:
                print 'No API call found for: ' + method
            else:
                result = method_call(*args)
                self.print_result(result)

        elif hasattr(ep_user, method):
            # User API
            method_call = getattr(ep_user, method)

            result = method_call(*args)
            self.print_result(result)

        elif hasattr(ep_admin, method):
            # Admin API
            method_call = getattr(ep_admin, method)

            result = method_call(*args)
            self.print_result(result)

        else:
            print 'No API call found for: ' + method

    def print_result(self, result):
        # Try to pretty-print (if json), otherwise print normally
        try:
            j = json.loads(result)
            print json.dumps(j, indent=2)
        except:
            print result


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        ExcaliburCmd().onecmd(' '.join(sys.argv[1:]))
    else:
        try:
            ExcaliburCmd().cmdloop(banner)
        except KeyboardInterrupt:
            print "Goodbye!"
