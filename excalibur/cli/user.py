#!/usr/bin/python3
import json

import base

class UserCLI(base.BaseCLI):

    def __init__(self, ip):
        super().__init__(ip)

        self.base_url = 'https://{0}:5002/virtue/user'.format(ip)

        self.commands['application get'] = self.app_get
        self.commands['role get'] = self.role_get
        self.commands['user role list'] = self.user_role_list
        self.commands['user virtue list'] = self.user_virtue_list
        self.commands['virtue get'] = self.virtue_get
        self.commands['virtue create'] = self.virtue_create
        self.commands['virtue launch'] = self.virtue_launch
        self.commands['virtue stop'] = self.virtue_stop
        self.commands['virtue destroy'] = self.virtue_destroy
        self.commands['virtue application launch'] = self.virtue_app_launch
        self.commands['virtue application stop'] = self.virtue_app_stop

    def app_get(self):

        app_id = input('Application ID: ').strip()

        result = self.session.get(self.base_url + '/application/get',
                                  params={'appId': app_id})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def role_get(self):

        role_id = input('Role ID: ').strip()

        result = self.session.get(self.base_url + '/role/get',
                                  params={'roleId': role_id})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def user_role_list(self):

        result = self.session.get(self.base_url + '/role/list')
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def user_virtue_list(self):

        result = self.session.get(self.base_url + '/virtue/list')
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def virtue_get(self):

        virtue_id = input('Virtue ID: ').strip()

        result = self.session.get(self.base_url + '/virtue/get',
                                  params={'virtueId': virtue_id})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def virtue_create(self):

        role_id = input('Role ID: ').strip()

        result = self.session.get(self.base_url + '/virtue/create',
                                  params={'roleId': role_id})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def virtue_launch(self):

        virtue_id = input('Virtue ID: ').strip()

        result = self.session.get(self.base_url + '/virtue/launch',
                                  params={'virtueId': virtue_id})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def virtue_stop(self):

        virtue_id = input('Virtue ID: ').strip()

        result = self.session.get(self.base_url + '/virtue/stop',
                                  params={'virtueId': virtue_id})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def virtue_destroy(self):

        virtue_id = input('Virtue ID: ').strip()

        result = self.session.get(self.base_url + '/virtue/destroy',
                                  params={'virtueId': virtue_id})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def virtue_app_launch(self):

        virtue_id = input('Virtue ID: ').strip()
        app_id = input('Application ID: ').strip()

        result = self.session.get(self.base_url + '/virtue/application/launch',
                                  params={
                                      'virtueId': virtue_id,
                                      'appId': app_id
                                  })
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def virtue_app_stop(self):

        virtue_id = input('Virtue ID: ').strip()
        app_id = input('Application ID: ').strip()

        result = self.session.get(self.base_url + '/virtue/application/stop',
                                  params={
                                      'virtueId': virtue_id,
                                      'appId': app_id
                                  })
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)
        

if (__name__ == '__main__'):

    cli = UserCLI(input('Excalibur address: ').strip())

    command = ''
    
    while (command != 'exit'):
        command = input('------- ')
        cli.handle_command(command)
