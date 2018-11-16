import json
import requests
import getpass

from sso_login import sso_tool

DEBUG = True

class BaseCLI:

    def __init__(self, ip, interactive_login=True):
        self.ip = ip
        self.sso = sso_tool(ip + ':5002')

        self.session = None

        if interactive_login:
            print(self.interactive_login())

        self.commands = {'help': self.help,
                         'exit': self.logout}

    def handle_command(self, command):

        command_tokens = command.split()

        real_command = ' '.join(command_tokens)

        if (real_command in self.commands):
            print(self.commands[real_command]())
        else:
            print('Unknown command: "{0}"'.format(real_command))

    def help(self):
        return '\n'.join(sorted(self.commands.keys()))

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
            return 'Failed to login'

        if (not self.get_token(app_name)):
            return 'Failed to login'

        return 'Successfully logged in'

    def logout(self):
        # Todo: Tell Excalibur to delete the token?
        self.session = None

        return 'Logged out'

    def get_token(self, app_name):

        redirect = 'https://{0}:5002/virtue/test'.format(self.ip)

        client_id = self.sso.get_app_client_id(app_name)
        if (client_id == None):
            client_id = self.sso.create_app(app_name, redirect)
            assert client_id

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
