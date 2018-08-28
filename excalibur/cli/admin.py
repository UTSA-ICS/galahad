#!/usr/bin/python3
import json

import base

#TODO: need to add exception handling if response cannot be jsonified
# received an error for data = result.json()
# received an error for:
'''
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='54.174.121.195', port=5002): Max retries exceeded with url: /virtue/admin/role/list (Caused by NewConnectionError('<requests.packages.urllib3.connection.VerifiedHTTPSConnection object at 0x7f19dd083780>: Failed to establish a new connection: [Errno 111] Connection refused',))
'''
'''
Traceback (most recent call last):
  File "/usr/lib/python3/dist-packages/requests/adapters.py", line 376, in send
    timeout=timeout
  File "/usr/lib/python3/dist-packages/urllib3/connectionpool.py", line 610, in urlopen
    _stacktrace=sys.exc_info()[2])
  File "/usr/lib/python3/dist-packages/urllib3/util/retry.py", line 247, in increment
    raise six.reraise(type(error), error, _stacktrace)
  File "/usr/lib/python3/dist-packages/six.py", line 685, in reraise
    raise value.with_traceback(tb)
  File "/usr/lib/python3/dist-packages/urllib3/connectionpool.py", line 560, in urlopen
    body=body, headers=headers)
  File "/usr/lib/python3/dist-packages/urllib3/connectionpool.py", line 379, in _make_request
    httplib_response = conn.getresponse()
  File "/usr/lib/python3.5/http/client.py", line 1197, in getresponse
    response.begin()
  File "/usr/lib/python3.5/http/client.py", line 297, in begin
    version, status, reason = self._read_status()
  File "/usr/lib/python3.5/http/client.py", line 266, in _read_status
    raise RemoteDisconnected("Remote end closed connection without"
requests.packages.urllib3.exceptions.ProtocolError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response',))

'''
'''
Traceback (most recent call last):
  File "admin.py", line 346, in <module>
    cli.handle_command(command)
  File "/home/senofsky/galahad/galahad/excalibur/cli/base.py", line 29, in handle_command
    print(self.commands[real_command]())
  File "admin.py", line 305, in valor_create
    result = self.session.get(self.base_url + '/valor/create')
  File "/usr/lib/python3/dist-packages/requests/sessions.py", line 480, in get
    return self.request('GET', url, **kwargs)
  File "/usr/lib/python3/dist-packages/requests/sessions.py", line 468, in request
    resp = self.send(prep, **send_kwargs)
  File "/usr/lib/python3/dist-packages/requests/sessions.py", line 576, in send
    r = adapter.send(request, **kwargs)
  File "/usr/lib/python3/dist-packages/requests/adapters.py", line 426, in send
    raise ConnectionError(err, request=request)
requests.exceptions.ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response',))
'''
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
        self.commands['virtue create'] = self.virtue_create
        self.commands['virtue destroy'] = self.virtue_destroy
        self.commands['valor list'] = self.valor_list
        self.commands['valor create'] = self.valor_create
        self.commands['valor create pool'] = self.valor_create_pool
#        self.commands['valor stop'] = self.valor_stop
        self.commands['valor destroy'] = self.valor_destroy

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

        ami_id = input('AMI ID for the new role (Optional): ')

        if (ami_id[:4] == 'ami-'):
            result = self.session.get(self.base_url + '/role/create',
                                      params={
                                          'role': json.dumps(role),
                                          'ami_id': ami_id
                                      })
        else:
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


    def virtue_create(self):

        username = input('Username: ').strip()
        role_id = input('Role ID: ').strip()

        result = self.session.get(self.base_url + '/virtue/create',
                                  params={'username': username,
                                          'roleId': role_id})
        data = result.json()

        return json.dumps(data, indent=4, sort_keys=True)


    def virtue_destroy(self):

        virtue_id = input('Virtue ID: ').strip()

        result = self.session.get(self.base_url + '/virtue/destroy',
                                  params={'virtueId': virtue_id})
        data = result.json()

        return json.dumps(data, indent=4, sort_keys=True)


    def valor_list(self):

        result = self.session.get(self.base_url + '/valor/list')

        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

 
    def valor_create(self):

        result = self.session.get(self.base_url + '/valor/create')

        data = result.json()

        return json.dumps(data, indent=4, sort_keys=True)


    def valor_create_pool(self):

        number_of_valors = input('Number of valors: ').strip()

        result = self.session.get(
            self.base_url + '/valor/create_pool',
            params={'number_of_valors': number_of_valors})

        data = result.json()

        return json.dumps(data, indent=4, sort_keys=True)


    def valor_destroy(self):

        valor_id = input('Valor ID: ').strip()

        result = self.session.get(
            self.base_url + '/valor/destroy',
            params={'valor_id': valor_id})

        data = result.json()

        return json.dumps(data, indent=4, sort_keys=True)


if (__name__ == '__main__'):

    cli = AdminCLI(input('Excalibur address: ').strip())

    command = ''

    while (command != 'exit'):
        command = input('------- ')
        cli.handle_command(command)
