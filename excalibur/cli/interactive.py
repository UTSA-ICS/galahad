#!/usr/bin/env python3

# Copyright (c) 2019 by Raytheon BBN Technologies Corp.
# Copyright (c) 2019 by Star Lab Corp.

# https://python-prompt-toolkit.readthedocs.io/en/stable/pages/tutorials/repl.html

from __future__ import unicode_literals
from enum import Enum

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, DynamicCompleter

from endpoint import Endpoint

import getpass
import sys


class InterpreterMode(Enum):
    BASE = 1
    USER = 2
    ADMIN = 3
    SECURITY = 4


class MetaCompleter:
    def __init__(self):
        pass

    def set_mode(self, _mode):
        self.mode = _mode

    def set_base_completer(self, base_completer):
        self.base_completer = base_completer

    def set_admin_completer(self, admin_completer):
        self.admin_completer = admin_completer

    def set_user_completer(self, user_completer):
        self.user_completer = user_completer

    def set_security_completer(self, completer):
        self.security_completer = completer

    def get_completer(self):
        if self.mode is InterpreterMode.BASE:
            return self.base_completer
        elif self.mode is InterpreterMode.USER:
            return self.user_completer
        elif self.mode is InterpreterMode.ADMIN:
            return self.admin_completer
        else:
            return self.base_completer


class ExcaliburCmd:
    def __init__(self, ip=None):
        self.base_ep = None
        self.admin_ep = None
        self.security_ep = None
        self.user_ep = None
        self.security_ep = None
        self.ip = ip

        self.mode = InterpreterMode.BASE

        # If you add a new endpoint, create a JSON file for it, then add it here
        self.admin_ep = Endpoint.factory(Endpoint.EpType.ADMIN, self.ip)
        self.user_ep = Endpoint.factory(Endpoint.EpType.USER, self.ip)
        self.security_ep = Endpoint.factory(Endpoint.EpType.SECURITY, self.ip)

        self.base_words = ['admin', 'user', 'security', 'login', 'exit']
        base_completer = WordCompleter(words=self.base_words, ignore_case=True)
        admin_completer = WordCompleter(words=self.admin_ep.commands.keys(), sentence=True)
        user_completer = WordCompleter(words=self.user_ep.commands.keys(), sentence=True)
        security_completer = WordCompleter(words=self.security_ep.commands.keys(), sentence=True)

        self.meta_completer = MetaCompleter()
        self.meta_completer.set_base_completer(base_completer)
        self.meta_completer.set_admin_completer(admin_completer)
        self.meta_completer.set_user_completer(user_completer)
        self.meta_completer.set_security_completer(security_completer)
        self.meta_completer.set_mode(InterpreterMode.BASE)

    def get_mode(self):
        return self.mode

    def set_mode(self, _mode):
        self.mode = _mode
        self.meta_completer.set_mode(_mode)

    def do_login(self):
        self.username = input('Email: ').strip()
        password = getpass.getpass('Password: ').strip()
        # ABJ: Uncomment this when it matters what the app name is
        # app_name = input('OAuth APP name (Default name \'APP_1\' Press Enter): ').strip()
        # if app_name == '':
        #    app_name = 'APP_1'
        app_name = 'APP_1'

        print('Logging in...')
        for ep in [self.admin_ep, self.user_ep, self.security_ep]:
            [res, msg] = ep.login(self.username, password, app_name)
            if not res:
                print('Error logging in to ' + str(ep) + ': ' + msg)
                break
        else:
            print('Login complete')

    def get_current_ep(self):
        if self.mode is InterpreterMode.USER:
            return self.user_ep
        elif self.mode is InterpreterMode.ADMIN:
            return self.admin_ep
        elif self.mode is InterpreterMode.SECURITY:
            return self.security_ep
        else:
            return self

    def handle_command(self, text):
        print('Unknown command: ' + text)

    def handle_cmd(self, text):
        if text == 'exit':
            if self.mode is InterpreterMode.BASE:
                raise EOFError
            else:
                self.set_mode(InterpreterMode.BASE)
                return

        # As a consequence of this, you have to bounce back through BASE
        # to switch from admin to user modes
        if self.mode is InterpreterMode.BASE:
            if text == 'user':
                print('Entering USER API mode...')
                self.set_mode(InterpreterMode.USER)
                return
            elif text == 'admin':
                print('Entering ADMIN API mode...')
                self.set_mode(InterpreterMode.ADMIN)
                return
            elif text == 'security':
                print('Entering SECURITY API mode...')
                self.set_mode(InterpreterMode.SECURITY)
                return

        if text == 'help':
            self.help()
            return
        elif text == 'login':
            self.do_login()
            return
        else:
            ret = self.get_current_ep().handle_command(text)
            if ret is not None:
                print('------------------')
                print(ret)
                print('------------------')

    def prompt_msg(self):
        '''Used by the PromptToolkit session to print the appropriate prompt message'''
        if self.mode is InterpreterMode.BASE:
            return '> '
        elif self.mode is InterpreterMode.USER:
            return '[USR]> '
        elif self.mode is InterpreterMode.ADMIN:
            return '[ADM]> '
        elif self.mode is InterpreterMode.SECURITY:
            return '[SEC]> '
        else:
            return '> '

    def help(self):
        mode_name = str(self.mode).split('.')[1]
        print('')
        print('The interpreter is currently in ' + mode_name + ' mode')
        print('To get back to BASE mode, press CTRL-C or type "exit"')
        print('')
        print('In ' + mode_name + ' mode, the available commands are:')
        if self.mode is InterpreterMode.BASE:
            for word in self.base_words:
                print('\t' + word)
        else:
            print(self.get_current_ep().help())


def main():
    server_address = '127.0.0.1'
    if len(sys.argv) is 2:
        server_address = sys.argv[1]
    else:
        print('WARNING - Using default Excalibur server address: {}'.format(server_address))

    excalibur = ExcaliburCmd(server_address)

    print('--------------------')
    print('Welcome to Excalibur')
    print('--------------------')
    print('Type "help" for more info, or type "exit" or press CTRL-D to exit')

    session = PromptSession()
    while True:
        try:
            text = session.prompt(
                excalibur.prompt_msg,
                completer=DynamicCompleter(excalibur.meta_completer.get_completer))
            excalibur.handle_cmd(text)
        except KeyboardInterrupt:
            if excalibur.get_mode() is InterpreterMode.BASE:
                break
            else:
                excalibur.set_mode(InterpreterMode.BASE)
        except EOFError:
            break

    print('Goodbye!')


if __name__ == '__main__':
    main()
