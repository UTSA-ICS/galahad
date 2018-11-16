#!/usr/bin/python3 

# https://python-prompt-toolkit.readthedocs.io/en/stable/pages/tutorials/repl.html

from __future__ import unicode_literals
from enum import Enum
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, DynamicCompleter

import admin
import base
import security
import user

class ExcaliburCmd:
    def __init__(self, ip=None):
        self.base_ep = None
        self.admin_ep = None
        self.security_ep = None
        self.user_ep = None
        self.security_ep = None
        self.ip = ip

    def connect(self, ip=None):
        if ip is not None:
            self.ip = ip

        if self.ip is None:
            return False

        self.admin_ep = admin.AdminCLI(self.ip, interactive=False)
        self.user_ep = user.UserCLI(self.ip, interactive=False)
        self.security_ep = security.SecurityCLI(self.ip, interactive=False)

    def get_admin_words(self):
        if self.admin_ep is None:
            return []
        else:
            return self.admin_ep.commands.keys()

    def get_user_words(self):
        if self.user_ep is None:
            return []
        else:
            return self.user_ep.commands.keys()

    def get_security_words(self):
        if self.security_ep is None:
            return []
        else:
            return self.security_ep.commands.keys()

class InterpreterMode(Enum):
    BASE = 1
    USER = 2
    ADMIN = 3
    SECURITY = 4

mode = InterpreterMode.BASE

def prompt_msg():
    if mode is InterpreterMode.BASE:
        return '> '
    elif mode is InterpreterMode.USER:
        return '[USR]> '
    elif mode is InterpreterMode.ADMIN:
        return '[ADM]> '
    elif mode is InterpreterMode.SECURITY:
        return '[SEC]> '
    else:
        return '> '

class MetaCompleter:
    def __init__(self):
        pass

    def set_base_completer(self, base_completer):
        self.base_completer = base_completer

    def set_admin_completer(self, admin_completer):
        self.admin_completer = admin_completer

    def set_user_completer(self, user_completer):
        self.user_completer = user_completer

    def set_security_completer(self, completer):
        self.security_completer = completer

    def get_completer(self):
        global mode
        if mode is InterpreterMode.BASE:
            return self.base_completer
        elif mode is InterpreterMode.USER:
            return self.user_completer
        elif mode is InterpreterMode.ADMIN:
            return self.admin_completer
        else:
            return self.base_completer

def main():
    global mode 

    session = PromptSession()
    excalibur = ExcaliburCmd('127.0.0.1')
    excalibur.connect()

    print('Welcome to Excalibur')
    print('Type "help" for more info, or type "exit" or press CTRL-D to exit')

    words = ['admin', 'user', 'security', 'login', 'exit']
    base_completer = WordCompleter(words=words, ignore_case=True)
    admin_completer = WordCompleter(words=excalibur.get_admin_words(), sentence=True)
    user_completer = WordCompleter(words=excalibur.get_user_words(), sentence=True)
    security_completer = WordCompleter(words=excalibur.get_security_words(), sentence=True)

    meta_completer = MetaCompleter()
    meta_completer.set_base_completer(base_completer)
    meta_completer.set_admin_completer(admin_completer)
    meta_completer.set_user_completer(user_completer)
    meta_completer.set_security_completer(security_completer)

    current_mode = InterpreterMode.BASE

    while True:
        try: 
            text = session.prompt(prompt_msg, completer=DynamicCompleter(meta_completer.get_completer))
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        else:
            if text == 'exit':
                if mode is InterpreterMode.BASE:
                    break
                else:
                    mode = InterpreterMode.BASE
            
            if mode is InterpreterMode.BASE:
                if text == 'user':
                    print('Entering USER API mode...')
                    mode = InterpreterMode.USER
                elif text == 'admin':
                    print('Entering ADMIN API mode...')
                    mode = InterpreterMode.ADMIN
                elif text == 'security':
                    print('Entering SECURITY API mode...')
                    mode = InterpreterMode.SECURITY
                    
            print('You entered: ', text)
    print('Goodbye!')

if __name__=='__main__':
    main()