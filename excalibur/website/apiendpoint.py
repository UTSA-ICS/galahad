# Copyright (c) 2019 by Star Lab Corp.

import copy
import json
import os
import shlex
import time
import traceback

from ldaplookup import LDAP
from services.errorcodes import ErrorCodes
from . import ldap_tools
from aws import AWS
from valor import ValorManager, RethinkDbManager, ResourceManager
from ssh_tool import ssh_tool

DEBUG_PERMISSIONS = False


class EndPoint():
    def __init__(self, user, password):
        self.inst = LDAP(user, password)

        self.inst.bind_ldap()

    # Retrieve information about the specified application
    def application_get(self, username, applicationId):

        try:
            if (not DEBUG_PERMISSIONS):

                user = self.inst.get_obj('cusername', username, 'openLDAPuser')
                if (user == None or user == ()):
                    # User was already validated, but can't be accessed now...
                    return json.dumps(ErrorCodes.user['unspecifiedError'])
                ldap_tools.parse_ldap(user)

            app = self.inst.get_obj('cid', applicationId,
                                    'openLDAPapplication', True)
            if (app == ()):
                return json.dumps(ErrorCodes.user['invalidId'])
            ldap_tools.parse_ldap(app)

            if (DEBUG_PERMISSIONS):
                return json.dumps(app)

            for roleId in user['authorizedRoleIds']:
                role = self.inst.get_obj('cid', roleId, 'openLDAProle')
                if (role == None or role == ()):
                    # Error!
                    continue
                ldap_tools.parse_ldap(role)

                if (applicationId in role['applicationIds']):
                    # User is authorized to access this application.
                    return json.dumps(app)

            return json.dumps(ErrorCodes.user['userNotAuthorized'])

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Retrieve data about the specified role
    def role_get(self, username, roleId):

        try:
            if (not DEBUG_PERMISSIONS):
                user = self.inst.get_obj('cusername', username, 'openLDAPuser')
                if (user == None or user == ()):
                    return json.dumps(ErrorCodes.user['unspecifiedError'])
                ldap_tools.parse_ldap(user)

            role = self.inst.get_obj('cid', roleId, 'openLDAProle', True)
            if (role == ()):
                return json.dumps(ErrorCodes.user['invalidId'])
            ldap_tools.parse_ldap(role)

            if (DEBUG_PERMISSIONS or roleId in user['authorizedRoleIds']):

                # Now get the IP address of the virtue associated with this user/role
                virtue_ip = 'NULL'

                ldap_virtues = self.inst.get_objs_of_type('OpenLDAPvirtue')
                virtues = ldap_tools.parse_ldap_list(ldap_virtues)

                for v in virtues:
                    if (v['username'] == username and v['roleId'] == roleId):
                        virtue_ip = v['ipAddress']
                        break

                role['ipAddress'] = virtue_ip

                return json.dumps(role)

            return json.dumps(ErrorCodes.user['userNotAuthorized'])

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Retrieve a list of roles available to user
    def user_role_list(self, username):

        try:
            user = self.inst.get_obj('cusername', username, 'openLDAPuser')
            if (user == None or user == ()):
                return json.dumps(ErrorCodes.user['unspecifiedError'])
            ldap_tools.parse_ldap(user)

            roles = []

            ldap_virtues = self.inst.get_objs_of_type('OpenLDAPvirtue')
            virtues = ldap_tools.parse_ldap_list(ldap_virtues)

            for roleId in user['authorizedRoleIds']:
                role = self.inst.get_obj('cid', roleId, 'openLDAProle')
                if (role == None or role == ()):
                    continue
                ldap_tools.parse_ldap(role)

                # Now get the IP address of the virtue associated with this user/role
                virtue_ip = 'NULL'

                for v in virtues:
                    if (v['username'] == username and v['roleId'] == roleId):
                        virtue_ip = v['ipAddress']
                        break

                role['ipAddress'] = virtue_ip

                roles.append(role)

            return json.dumps(roles)

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Retrieve a list of virtues available to user
    def user_virtue_list(self, username):

        try:
            virtues_raw = self.inst.get_objs_of_type('OpenLDAPvirtue')
            if (virtues_raw == None):
                return json.dumps(ErrorCodes.user['unspecifiedError'])

            virtues_ret = []

            for virtue in virtues_raw:
                ldap_tools.parse_ldap(virtue[1])

                if (virtue[1]['username'] == username):
                    virtues_ret.append(virtue[1])

            return json.dumps(virtues_ret)

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Retrieve information about the specified virtue
    def virtue_get(self, username, virtueId):

        try:
            virtue = self.inst.get_obj('cid', virtueId, 'OpenLDAPvirtue', True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.user['invalidId'])
            ldap_tools.parse_ldap(virtue)

            if (virtue['username'] == username or DEBUG_PERMISSIONS):
                return json.dumps(virtue)

            return json.dumps(ErrorCodes.user['userNotAuthorized'])

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    def virtue_reload_state(self, username, virtueId):

        try:
            virtue = self.inst.get_obj('cid', virtueId, 'OpenLDAPvirtue', True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.user['invalidId'])
            ldap_tools.parse_ldap(virtue)

            updated_virtue = copy.deepcopy(virtue)

            if (virtue['username'] != username):
                return json.dumps(ErrorCodes.user['userNotAuthorized'])

            rdb_manager = RethinkDbManager()
            rdb_virtue = rdb_manager.get_virtue(virtueId)
            if (rdb_virtue == None):
                updated_virtue['state'] = 'STOPPED'
                updated_virtue['ipAddress'] = 'NULL'
            else:
                updated_virtue['state'] = 'RUNNING'
                updated_virtue['ipAddress'] = rdb_virtue['guestnet']

            if (updated_virtue != virtue):
                ldap_virtue = ldap_tools.to_ldap(updated_virtue, 'OpenLDAPvirtue')
                self.inst.modify_obj('cid', virtueId, ldap_virtue,
                                     'OpenLDAPvirtue', True)

            return json.dumps(ErrorCodes.user['success'])

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Launch the specified virtue, which must have already been created
    def virtue_launch(self, username, virtueId, use_valor=True):

        try:
            virtue = self.inst.get_obj('cid', virtueId, 'OpenLDAPvirtue', True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.user['invalidId'])
            ldap_tools.parse_ldap(virtue)

            if (virtue['username'] != username):
                return json.dumps(ErrorCodes.user['userNotAuthorized'])

            if ('RUNNING' in virtue['state']
                    or virtue['state'] == 'LAUNCHING'):
                return json.dumps(ErrorCodes.user['virtueAlreadyLaunched'])
            elif (virtue['state'] != 'STOPPED'):
                return json.dumps(
                    ErrorCodes.user['virtueStateCannotBeLaunched'])

            if (use_valor):
                valor_manager = ValorManager()

                valor = valor_manager.get_empty_valor()

                try:
                    virtue['ipAddress'] = valor_manager.add_virtue(
                        valor['address'],
                        valor['valor_id'],
                        virtue['id'],
                        'images/provisioned_virtues/' + virtue['id'] + '.img')

                except AssertionError:
                    return json.dumps(ErrorCodes.user['virtueAlreadyLaunched'])

            virtue['state'] = 'LAUNCHING'
            ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
            self.inst.modify_obj('cid', virtue['id'], ldap_virtue,
                                 objectClass='OpenLDAPvirtue', throw_error=True)

            # wait until sshable
            success = False
            max_attempts = 5

            # TODO: Remove this variable before merging into master
            see_no_evil = False

            if not use_valor:
                virtue['state'] = 'RUNNING'
            elif see_no_evil:
                virtue['state'] = 'RUNNING (Unverified)'
            else:

                for attempt_number in range(max_attempts):

                    try:

                        time.sleep(30)

                        ssh = ssh_tool(
                            'virtue', virtue['ipAddress'],
                            os.environ['HOME'] + '/user-keys/default-virtue-key.pem')
                        ssh.ssh('echo test')

                        print('Successfully connected to {}'.format(
                            virtue['ipAddress']))

                        # KL --- add if resIDs not empty run:
                        # Kerberos tgt setup for resource management
                        if len(virtue['resourceIds']) is not 0:
                            krb5cc_src = '/tmp/krb5cc_{}'.format(username)
                            krb5cc_dest = '/tmp/krb5cc_0'

                            ssh.scp_to(krb5cc_src, krb5cc_dest)

                            role = self.inst.get_obj('cid', virtue['roleId'], 'openLDAProle')
                            ldap_tools.parse_ldap(role)

                            for res in virtue['resourceIds']:
                                resource = self.inst.get_obj('cid', res, 'openLDAPresource')
                                ldap_tools.parse_ldap(resource)
                                resource_manager = ResourceManager(username, resource)
                                getattr(resource_manager, resource['type'].lower())(
                                    virtue['ipAddress'],
                                    os.environ['HOME'] + '/user-keys/default-virtue-key.pem',
                                    role['applicationIds'])


                        success = True

                        break

                    except Exception as e:
                        print(e)
                        print('Attempt {0} failed to connect').format(attempt_number+1)

                if (not success):
                    valor_manager.rethinkdb_manager.remove_virtue(virtue['id'])
                    virtue['state'] = 'STOPPED'
                    ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
                    self.inst.modify_obj(
                        'cid', virtue['id'], ldap_virtue,
                        objectClass='OpenLDAPvirtue', throw_error=True)
                    return json.dumps(ErrorCodes.user['serverLaunchError'])

                virtue['state'] = 'RUNNING'

            ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
            self.inst.modify_obj('cid', virtue['id'], ldap_virtue,
                                 objectClass='OpenLDAPvirtue', throw_error=True)

            return json.dumps(ErrorCodes.user['success'])

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Stop the specified virtue, but do not destroy it
    def virtue_stop(self, username, virtueId, use_valor=True):

        try:
            virtue = self.inst.get_obj('cid', virtueId, 'OpenLDAPvirtue', True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.user['invalidId'])
            ldap_tools.parse_ldap(virtue)

            if (virtue['username'] != username):
                return json.dumps(ErrorCodes.user['userNotAuthorized'])

            if (virtue['state'] == 'STOPPED'):
                return json.dumps(ErrorCodes.user['virtueAlreadyStopped'])
            elif ('RUNNING' not in virtue['state']):
                return json.dumps(
                    ErrorCodes.user['virtueStateCannotBeStopped'])

            try:
                if (use_valor):

                    if len(virtue['resourceIds']) is not 0:
                        role = self.inst.get_obj('cid', virtue['roleId'], 'openLDAProle')
                        ldap_tools.parse_ldap(role)

                        for res in virtue['resourceIds']:
                            resource = self.inst.get_obj('cid', res, 'openLDAPresource')
                            ldap_tools.parse_ldap(resource)
                            resource_manager = ResourceManager(username, resource)
                            call = 'remove_' + resource['type'].lower()
                            getattr(resource_manager, call)(
                                virtue['ipAddress'],
                                os.environ['HOME'] + '/user-keys/default-virtue-key.pem',
                                role['applicationIds'])

                        ssh = ssh_tool('virtue', virtue['ipAddress'],
                                       os.environ['HOME'] + \
                                       '/user-keys/default-virtue-key.pem')

                        ssh.ssh('sudo rm /tmp/krb5cc_0')

                    rdb_manager = RethinkDbManager()
                    rdb_manager.remove_virtue(virtue['id'])
            except AssertionError:
                return json.dumps(ErrorCodes.user['serverStopError'])
            except:
                print('Error:\n{}'.format(traceback.format_exc()))
                return json.dumps(ErrorCodes.user['unspecifiedError'])
            else:
                virtue['state'] = 'STOPPED'
                ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
                self.inst.modify_obj(
                    'cid', virtue['id'], ldap_virtue,
                    objectClass='OpenLDAPvirtue', throw_error=True)

            return json.dumps(ErrorCodes.user['success'])

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Launch an application on the specified virtue
    def virtue_application_launch(self, username, virtueId, applicationId, use_ssh=True):

        try:
            virtue = self.inst.get_obj('cid', virtueId, 'OpenLDAPvirtue', True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.user['invalidVirtueId'])
            ldap_tools.parse_ldap(virtue)

            if (virtue['username'] != username):
                return json.dumps(ErrorCodes.user['userNotAuthorized'])

            if ('RUNNING' not in virtue['state'] and use_ssh):
                return json.dumps(ErrorCodes.user['virtueNotRunning'])

            app = self.inst.get_obj('cid', applicationId,
                                    'OpenLDAPapplication', True)
            if (app == ()):
                return json.dumps(ErrorCodes.user['invalidApplicationId'])
            ldap_tools.parse_ldap(app)

            role = self.inst.get_obj('cid', virtue['roleId'], 'OpenLDAProle')
            if (role == None or role == ()):
                return json.dumps(ErrorCodes.user['unspecifiedError'])
            ldap_tools.parse_ldap(role)

            if (app['id'] not in role['applicationIds']):
                return json.dumps(ErrorCodes.user['applicationNotInVirtue'])

            if (app['id'] in virtue['applicationIds']):
                return json.dumps(
                    ErrorCodes.user['applicationAlreadyLaunched'])

            if (use_ssh):
                ssh = ssh_tool('virtue', virtue['ipAddress'],
                               '{0}/user-keys/{1}.pem'.format(
                                   os.environ['HOME'], username))

                start_docker_container = ('sudo docker start $(sudo docker ps' +
                                          ' -af name="{0}" -q)').format(
                                              app['id'])

                # Copy the network Rules file.
                copy_network_rules = (
                    'sudo docker cp /etc/networkRules $(sudo docker ps -af' +
                    ' name="{0}" -q):/etc/networkRules').format(app['id'])
                ssh.ssh(copy_network_rules)

                # Copy the authorized keys file
                auth_keys_path = '/home/virtue/.ssh/authorized_keys'
                copy_authorized_keys_cmd = (
                    'sudo docker cp {0}'
                    ' $(sudo docker ps -af name="{1}" -q):'
                    '{0}').format(auth_keys_path, app['id'])
                ssh.ssh(copy_authorized_keys_cmd)

                docker_exit = ssh.ssh(start_docker_container,
                                      test=False, silent=True)

                if (docker_exit != 0):
                    # This is an issue with docker where if the docker daemon exits
                    # uncleanly then a system file is locked and docker start fails
                    # with the error:
                    #     Error response from daemon: id already in use
                    #     Error: failed to start containers:
                    # The current workaround is to issue the docker start command
                    # twice. Tne first time it fails with the above error and the
                    # second time it succeeds.
                    docker_exit = ssh.ssh(start_docker_container, test=False)
                if (docker_exit != 0):
                    print(
                        "Docker start command for launching application {} Failed".format(
                            app['id']))
                    return json.dumps(ErrorCodes.user['serverLaunchError'])

                docker_chown_cmd = (
                    'sudo docker exec $(sudo docker ps -af name="{0}" -q)'
                    ' $(which chown) virtue:virtue {1}').format(
                        app['id'], auth_keys_path)
                ssh.ssh(docker_chown_cmd)

            virtue['applicationIds'].append(applicationId)

            del virtue['state']
            del virtue['ipAddress']

            ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')

            assert 0 == self.inst.modify_obj('cid', virtue['id'], ldap_virtue,
                                             objectClass='OpenLDAPvirtue',
                                             throw_error=True)

            return json.dumps(ErrorCodes.user['success'])

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Stop an application on the specified virtue
    def virtue_application_stop(self, username, virtueId, applicationId, use_ssh=True):

        try:
            virtue = self.inst.get_obj('cid', virtueId, 'OpenLDAPvirtue', True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.user['invalidVirtueId'])
            ldap_tools.parse_ldap(virtue)

            if (virtue['username'] != username):
                return json.dumps(ErrorCodes.user['userNotAuthorized'])

            if ('RUNNING' not in virtue['state'] and use_ssh):
                return json.dumps(ErrorCodes.user['virtueNotRunning'])

            app = self.inst.get_obj('cid', applicationId,
                                    'OpenLDAPapplication', True)
            if (app == ()):
                return json.dumps(ErrorCodes.user['invalidApplicationId'])
            ldap_tools.parse_ldap(app)

            role = self.inst.get_obj('cid', virtue['roleId'], 'OpenLDAProle')
            if (role == None or role == ()):
                return json.dumps(ErrorCodes.user['unspecifiedError'])
            ldap_tools.parse_ldap(role)

            if (app['id'] not in role['applicationIds']):
                return json.dumps(ErrorCodes.user['applicationNotInVirtue'])

            if (app['id'] not in virtue['applicationIds']):
                return json.dumps(ErrorCodes.user['applicationAlreadyStopped'])

            if (use_ssh):
                ssh = ssh_tool('virtue', virtue['ipAddress'],
                               '{0}/user-keys/{1}.pem'.format(
                                   os.environ['HOME'], username))

                docker_exit = ssh.ssh(('sudo docker stop $(sudo docker ps -af '
                                       'name="{0}" -q)').format(app['id']),
                                      test=False)

                if (docker_exit != 0):
                    return json.dumps(ErrorCodes.user['serverStopError'])

            virtue['applicationIds'].remove(applicationId)

            del virtue['state']
            del virtue['ipAddress']

            ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')

            assert 0 == self.inst.modify_obj('cid', virtue['id'], ldap_virtue,
                                             objectClass='OpenLDAPvirtue',
                                             throw_error=True)

            return json.dumps(ErrorCodes.user['success'])

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    def key_get(self, username):

        try:
            with open('{0}/user-keys/{1}.pem'.format(
                    os.environ['HOME'], username), 'r') as keyfile:
                data = keyfile.read()

            return json.dumps(data)

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])


if (__name__ == '__main__'):

    ep = EndPoint('slapd@virtue.gov', 'Test123!')

    print(ep.inst.query_ldap('cn', 'slapd'))

    fake_token = {
        'username': 'slapd',
        'token': 3735928559,
        'expiration': 0
    }

    print(ep.application_get(fake_token, 'firefox1'))
    print(ep.role_get(fake_token, 'Test'))
    print(ep.user_role_list(fake_token))
    print(ep.user_virtue_list(fake_token))
    print(ep.virtue_get(fake_token, 'TestVirtue'))
