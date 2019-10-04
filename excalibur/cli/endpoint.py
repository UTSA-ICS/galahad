#!/usr/bin/python3

# Copyright (c) 2019 by Star Lab Corp.

from enum import Enum
from sso_login import sso_tool

import getpass
import json
import requests

DEBUG = True


class Endpoint(object):

    class EpType(Enum):
        ADMIN = 1
        USER = 2
        SECURITY = 3

    def factory(_type, ip):
        if not isinstance(_type, Endpoint.EpType):
            raise TypeError("Please use an Endpoint.EpType")

        ep = Endpoint(ip)

        cmdfile = None
        if _type == Endpoint.EpType.ADMIN:
            cmdfile = 'admin_api.json'
        elif _type == Endpoint.EpType.USER:
            cmdfile = 'user_api.json'
        elif _type == Endpoint.EpType.SECURITY:
            cmdfile = 'security_api.json'
        else:
            raise NotImplementedError("Unknown type: " + repr(_type))

        with open(cmdfile, 'r') as cmdfile:
            cmd_json = json.loads(cmdfile.read())
            ep.base_url = cmd_json['base_url'].format(ip)
            for cmd in cmd_json['commands']:
                ep.commands[cmd['command']] = cmd
        return ep
    factory = staticmethod(factory)

    def __init__(self, ip):
        self.ip = ip
        self.sso = sso_tool(ip + ':5002')
        self.session = None
        self.commands = {'help': {"help": "Get help"},
                         'exit': {"help": "Return to BASE mode or exit"}}

    def handle_command(self, command, _params=None):
        if command == 'help':
            print(self.help())
            return None

        command_tokens = command.split()
        real_command = ' '.join(command_tokens)
        cmd = self.commands.get(real_command, None)

        if cmd is None:
            print('Unknown command: "{0}"'.format(real_command))
            return None

        if self.session is None:
            return 'Please log in before issuing any commands'

        # If the params dictionary is missing, then prompt the user
        params = _params
        if params is None:
            params = {}
            for param in cmd['parameters']:

                if param.get('optional'):
                    prompt_text = param['name'] + ' (Optional): '
                else:
                    prompt_text = param['name'] + ': '

                param_value = input(prompt_text)
                if (param_value):
                    params[param['url_name']] = param_value

        # Check for missing parameters
        missing_params = []
        for param in cmd['parameters']:
            if not param['url_name'] in params and not param.get('optional'):
                missing_params.append(param['url_name'])

        if len(missing_params) != 0:
            return '{\n    "missing_parameters": [ %s ] \n}' % (', '.join(['"%s"' % s for s in missing_params]))

        # Convert file parameters into their contents
        for param in cmd['parameters']:
            if 'is_file' in param:
                argument = param['url_name']
                with open(params[argument], 'r') as param_file:
                    params[argument] = param_file.read()

        # Print out the request parameters
        # print(json.dumps(params, indent=4))

        result = self.session.get(self.base_url + cmd['url'], params=params)
        data = result.json()
        return json.dumps(data, indent=4, sort_keys=True)

    def help(self):
        msg = ""
        for c in sorted(self.commands.keys()):
            msg += "\t{0:26} {1}\n".format(c, self.commands[c]['help'])
        return msg

    def interactive_login(self):
        self.username = input('Email: ').strip()
        password = getpass.getpass('Password: ').strip()

        app_name = input('OAuth APP name (Default name \'APP_1\' Press Enter): ').strip()

        if app_name == '':
            app_name = 'APP_1'

        self.logout()

        if (not self.sso.login(self.username, password)):
            return 'Failed to login'

        if (not self.get_token(app_name)):
            return 'Failed to login'

        return 'Successfully logged in'

    def login(self, username, password, app_name="APP_1"):
        self.username = username
        if app_name == '':
            app_name = 'APP_1'

        self.logout()

        if (not self.sso.login(self.username, password)):
            return [False, 'Failed to login']

        if (not self.get_token(app_name)):
            return [False, 'Failed to login']

        return [True, 'Successfully logged in']

    def logout(self):
        # Todo: Tell Excalibur to delete the token?
        self.session = None

        return 'Logged out'

    def set_token(self, token):
        # If you use sso_login.py from a script, you can call set_token directly
        # without going through the login process
        self.session = requests.Session()
        self.session.headers = {
            'Authorization': 'Bearer {0}'.format(token['access_token'])
        }
        self.session.verify = not DEBUG

    def get_token(self, app_name):

        redirect = 'https://{}:5002/virtue/test'.format(self.ip)
        redirect_canvas = 'https://{}:5002/virtue/test\n' \
                          'http://canvas.com:3000/connect/excalibur/callback'.format(self.ip)

        client_id = self.sso.get_app_client_id(app_name)
        if (client_id == None):
            client_id = self.sso.create_app(app_name, redirect_canvas)
            assert client_id

        code = self.sso.get_oauth_code(client_id, redirect)

        if (code == None):
            print('Could not retrieve access code')
            return False

        token = self.sso.get_oauth_token(client_id, code, redirect)

        if (token == None):
            print('Could not retrieve token')
            return False

        self.set_token(token)

        return True


if __name__ == '__main__':
    ep = Endpoint.factory(Endpoint.EpType.USER, "127.0.0.1")
    ep.login("slapd@virtue.gov", "Test123!", "APP_1")
