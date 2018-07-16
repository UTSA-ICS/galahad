#!/usr/bin/python3
import json

import base

class AdminCLI(base.BaseCLI):

    def __init__(self, ip):
        super().__init__(ip)

        self.base_url = 'https://{0}:5002/virtue/admin'.format(ip)

        self.commands['application list'] = self.app_list
        self.commands['resource get'] = self.resource_get
        self.commands['resource list'] = self.resource_list
        self.commands['resource attach'] = self.resource_attach
        self.commands['resource detach'] = self.resource_detach
        self.commands['role create'] = self.role_create
        self.commands['role list'] = self.role_list
        self.commands['system export'] = self.system_export
        self.commands['system import'] = self.system_import
        self.commands['test import user'] = self.test_import_user
        self.commands['test import application'] = self.test_import_app
        self.commands['test import role'] = self.test_import_role
        self.commands['user list'] = self.user_list
        self.commands['user get'] = self.user_get
        self.commands['user virtue list'] = self.user_virtue_list
        self.commands['user logout'] = self.user_logout
        self.commands['user role authorize'] = self.user_role_auth
        self.commands['user role unauthorize'] = self.user_role_unauth
        
        #self.commands['usertoken list'] = self.usertoken_list

    def app_list(self):

        result = self.session.get(self.base_url + '/application/list')
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def resource_get(self):

        resource_id = input('Resource ID: ').strip()

        result = self.session.get(self.base_url + '/resource/get',
                                  params={'resourceId': resource_id})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def resource_list(self):

        result = self.session.get(self.base_url + '/resource/list')
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def resource_attach(self):

        resource_id = input('Resource ID: ').strip()
        virtue_id = input('Virtue ID: ').strip()

        result = self.session.get(self.base_url + '/resource/attach',
                                  params={'resourceId': resource_id,
                                          'virtueId': virtue_id
                                  })
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def resource_detach(self):

        resource_id = input('Resource ID: ').strip()
        virtue_id = input('Virtue ID: ').strip()

        result = self.session.get(self.base_url + '/resource/detach',
                                  params={'resourceId': resource_id,
                                          'virtueId': virtue_id
                                  })
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def role_create(self):

        role_path = input('Role configuration file (json): ')

        try:
            with open(role_path, 'r') as json_file:
                role = json.load(json_file)
        except FileNotFoundError:
            return '{0} does not exist.'.format(role_path)
        except IsADirectoryError:
            return '{0} is a directory.'.format(role_path)
        except json.decoder.JSONDecodeError:
            return 'Json file has invalid format.'

        result = self.session.get(self.base_url + '/role/create',
                                  params={'role': json.dumps(role)})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def role_list(self):

        result = self.session.get(self.base_url + '/role/list')
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def system_export(self):

        result = self.session.get(self.base_url + '/system/export')
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def system_import(self):

        data_path = input('Path to .json file: ')

        try:
            with open(data_path, 'r') as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            return '{0} does not exist.'.format(data_path)
        except IsADirectoryError:
            return '{0} is a directory.'.format(data_path)
        except json.decoder.JSONDecodeError:
            return 'Json file has invalid format.'

        result = self.session.get(self.base_url + '/system/import',
                                  params={'data': json.dumps(data)})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def test_import_user(self):

        which = input('Which: ').strip()

        result = self.session.get(self.base_url + '/test/import/user',
                                  params={'which': which})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def test_import_app(self):

        which = input('Which: ').strip()

        result = self.session.get(self.base_url + '/test/import/application',
                                  params={'which': which})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def test_import_role(self):

        which = input('Which: ').strip()

        result = self.session.get(self.base_url + '/test/import/role',
                                  params={'which': which})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)
    
    def user_list(self):

        result = self.session.get(self.base_url + '/user/list')
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)
    
    def user_get(self):

        user = input('Username: ').strip()

        result = self.session.get(self.base_url + '/user/get',
                                  params={'username': user})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def user_virtue_list(self):

        user = input('Username: ').strip()

        result = self.session.get(self.base_url + '/user/virtue/list',
                                  params={'username': user})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def user_logout(self):

        user = input('Username: ').strip()

        result = self.session.get(self.base_url + '/user/logout',
                                  params={'username': user})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def user_role_auth(self):

        user = input('Username: ').strip()
        role = input('Role ID: ').strip()

        result = self.session.get(self.base_url + '/user/role/authorize',
                                  params={'username': user,
                                          'roleId': role})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def user_role_unauth(self):

        user = input('Username: ').strip()
        role = input('Role ID: ').strip()

        result = self.session.get(self.base_url + '/user/role/unauthorize',
                                  params={'username': user,
                                          'roleId': role})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

if (__name__ == '__main__'):

    cli = AdminCLI(input('Excalibur address: ').strip())

    command = ''
    
    while (command != 'exit'):
        command = input('------- ')
        cli.handle_command(command)
