import json
import requests
import getpass

from sso_login import sso_tool

DEBUG = True

class BaseCLI:

    def __init__(self, ip):
        self.ip = ip
        self.sso = sso_tool(ip + ':5002')

        self.session = None

        print(self.login())

        self.commands = {'exit': self.logout}

    def handle_command(self, command):

        command_tokens = command.split()

        real_command = ' '.join(command_tokens)

        if (real_command in self.commands):
            print(self.commands[real_command]())
        else:
            print('Unknown command: "{0}"'.format(real_command))

    def login(self):
        self.username = input('Email: ').strip()
        password = getpass.getpass('Password: ').strip()
        client_id = input('Client ID: ').strip()
        self.logout()

        if (not self.sso.login(self.username, password)):
            return 'Failed to login'

        if (not self.get_token(client_id)):
            return 'Failed to login'

        return 'Successfully logged in'

    def logout(self):
        # Todo: Tell Excalibur to delete the token?
        self.session = None

        return 'Logged out'

    def get_token(self, client_id):

        redirect = 'https://{0}:5002/virtue/test'.format(self.ip)

        code = self.sso.get_oauth_code(client_id, redirect)

        if (code == None):
            print('Could not retrieve access code')
            return False

        token = self.sso.get_oauth_token(client_id, code, redirect)

        if (token == None):
            print('Could not retrieve token')
            return False

        self.session = requests.Session()
        self.session.headers = {
            'Authorization': 'Bearer {0}'.format(token['access_token'])
        }
        self.session.verify = not DEBUG

        return True
