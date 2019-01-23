import os
import shutil
import json
import random
import time
import copy
import traceback
import subprocess
import base64
import requests
from zipfile import ZipFile

from ldaplookup import LDAP
from services.errorcodes import ErrorCodes
from apiendpoint import EndPoint
from controller import CreateVirtueThread, AssembleRoleThread
from . import ldap_tools
from aws import AWS
from valor import ValorAPI, RethinkDbManager

from assembler.assembler import Assembler

DEBUG_PERMISSIONS = False


class EndPoint_Admin():

    def __init__(self, user, password):

        self.inst = LDAP(user, password)
        self.inst.bind_ldap()
        self.valor_api = ValorAPI()
        self.rdb_manager = RethinkDbManager()


    def application_list(self):

        try:
            ldap_applications = self.inst.get_objs_of_type(
                'OpenLDAPapplication')
            assert ldap_applications != None

            applications = ldap_tools.parse_ldap_list(ldap_applications)

            return json.dumps(applications)

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])


    def resource_get(self, resourceId):

        try:
            resource = self.inst.get_obj(
                'cid',
                resourceId,
                objectClass='OpenLDAPresource',
                throw_error=True)
            if (resource == ()):
                return json.dumps(ErrorCodes.admin['invalidId'])
            ldap_tools.parse_ldap(resource)

            return json.dumps(resource)

        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def resource_list(self):

        try:
            ldap_resources = self.inst.get_objs_of_type('OpenLDAPresource')
            assert ldap_resources != None

            resources = ldap_tools.parse_ldap_list(ldap_resources)

            return json.dumps(resources)

        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def resource_attach(self, resourceId, virtueId):

        try:
            resource = self.inst.get_obj(
                'cid',
                resourceId,
                objectClass='OpenLDAPresource',
                throw_error=True)
            if (resource == ()):
                return json.dumps(ErrorCodes.admin['invalidResourceId'])
            ldap_tools.parse_ldap(resource)

            virtue = self.inst.get_obj(
                'cid',
                virtueId,
                objectClass='OpenLDAPvirtue',
                throw_error=True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.admin['invalidVirtueId'])
            ldap_tools.parse_ldap(virtue)

            if (virtue['state'] == 'DELETING'):
                return json.dumps(ErrorCodes.admin['invalidVirtueState'])

            if (resourceId in virtue['resourceIds']):
                return json.dumps(ErrorCodes.admin['cantAttach'])

            return json.dumps(ErrorCodes.admin['notImplemented'])

        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def resource_detach(self, resourceId, virtueId):

        try:
            resource = self.inst.get_obj(
                'cid',
                resourceId,
                objectClass='OpenLDAPresource',
                throw_error=True)
            if (resource == ()):
                return json.dumps(ErrorCodes.admin['invalidResourceId'])
            ldap_tools.parse_ldap(resource)

            virtue = self.inst.get_obj(
                'cid',
                virtueId,
                objectClass='OpenLDAPvirtue',
                throw_error=True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.admin['invalidVirtueId'])
            ldap_tools.parse_ldap(virtue)

            if (resourceId not in virtue['resourceIds']):
                return json.dumps(ErrorCodes.admin['cantDetach'])

            return json.dumps(ErrorCodes.admin['notImplemented'])
        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def role_create(
        self,
        role,
        use_ssh=True,
        hard_code_path='images/unities/4GB.img'):

        # TODO: Assemble on a running VM

        try:
            role_keys = [
                'name',
                'version',
                'applicationIds',
                'startingResourceIds',
                'startingTransducerIds'
            ]
            if (set(role.keys()) != set(role_keys)
                    and set(role.keys()) != set(role_keys + ['id'])):
                return json.dumps(ErrorCodes.admin['invalidFormat'])

            if (not isinstance(role['name'], basestring)
                    or not isinstance(role['version'], basestring)
                    or type(role['applicationIds']) != list
                    or type(role['startingResourceIds']) != list
                    or type(role['startingTransducerIds']) != list):
                return json.dumps(ErrorCodes.admin['invalidFormat'])

            if not role['applicationIds']:
                return json.dumps(ErrorCodes.admin['NoApplicationId'])

            for a in role['applicationIds']:
                app_test = self.inst.get_obj(
                    'cid',
                    a,
                    objectClass='OpenLDAPapplication',
                    throw_error=True)
                if (app_test == ()):
                    return json.dumps(ErrorCodes.admin['invalidApplicationId'])

            for r in role['startingResourceIds']:
                res_test = self.inst.get_obj(
                    'cid', r, objectClass='OpenLDAPresource', throw_error=True)
                if (res_test == ()):
                    return json.dumps(ErrorCodes.admin['invalidResourceId'])

            for t in role['startingTransducerIds']:
                tr_test = self.inst.get_obj(
                    'cid',
                    t,
                    objectClass='OpenLDAPtransducer',
                    throw_error=True)
                if (tr_test == ()):
                    return json.dumps(ErrorCodes.admin['invalidTransducerId'])

            new_role = copy.deepcopy(role)

            new_role['id'] = '{0}{1}'.format(new_role['name'], int(time.time()))

            try:
                # Call a controller thread to create and assemble the new image
                thr = AssembleRoleThread(self.inst.email, self.inst.password,
                                         new_role, hard_code_path,
                                         use_ssh=use_ssh)
            except AssertionError:
                return json.dumps(ErrorCodes.admin['storageError'])
            thr.start()

            return json.dumps({'id': new_role['id'], 'name': new_role['name']})

        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def role_list(self):

        try:
            ldap_roles = self.inst.get_objs_of_type('OpenLDAProle')
            assert ldap_roles != None

            roles = ldap_tools.parse_ldap_list(ldap_roles)

            return json.dumps(roles)

        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def system_export(self):
        return json.dumps(ErrorCodes.admin['notImplemented'])

    def system_import(self, data):
        return json.dumps(ErrorCodes.admin['notImplemented'])

    def test_import_user(self, which):
        return json.dumps(ErrorCodes.admin['notImplemented'])

    def test_import_application(self, which):
        return json.dumps(ErrorCodes.admin['notImplemented'])

    def test_import_role(self, which):
        return json.dumps(ErrorCodes.admin['notImplemented'])

    def user_list(self):

        try:
            ldap_users = self.inst.get_objs_of_type('OpenLDAPuser')
            assert ldap_users != None

            users = ldap_tools.parse_ldap_list(ldap_users)

            return json.dumps(users)

        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def user_get(self, username):

        try:
            user = self.inst.get_obj(
                'cusername',
                username,
                objectClass='OpenLDAPuser',
                throw_error=True)
            if (user == ()):
                return json.dumps(ErrorCodes.admin['invalidUsername'])
            ldap_tools.parse_ldap(user)

            return json.dumps(user)

        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def user_virtue_list(self, username):

        user = self.inst.get_obj(
            'cusername', username, objectClass='OpenLDAPuser')
        if (user == ()):
            return json.dumps(ErrorCodes.admin['invalidUsername'])
        elif (user == None):
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

        ep = EndPoint(self.inst.email, self.inst.password)

        return ep.user_virtue_list(username)

    def user_role_authorize(self, username, roleId):

        try:
            user = self.inst.get_obj(
                'cusername',
                username,
                objectClass='OpenLDAPuser',
                throw_error=True)
            if (user == ()):
                return json.dumps(ErrorCodes.admin['invalidUsername'])
            ldap_tools.parse_ldap(user)

            role = self.inst.get_obj(
                'cid', roleId, objectClass='OpenLDAProle', throw_error=True)
            if (role == ()):
                if (roleId in user['authorizedRoleIds']):
                    # The user is authorized for a nonexistant role...
                    # Remove it from their list?
                    1 + 1
                return json.dumps(ErrorCodes.admin['invalidRoleId'])
            ldap_tools.parse_ldap(role)

            if (roleId in user['authorizedRoleIds']):
                return json.dumps(ErrorCodes.admin['userAlreadyAuthorized'])

            user['authorizedRoleIds'].append(roleId)

            ldap_user = ldap_tools.to_ldap(user, 'OpenLDAPuser')

            self.inst.modify_obj(
                'cusername',
                username,
                ldap_user,
                objectClass='OpenLDAPuser',
                throw_error=True)

            return json.dumps(ErrorCodes.admin['success'])

        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def user_role_unauthorize(self, username, roleId):

        try:
            user = self.inst.get_obj(
                'cusername',
                username,
                objectClass='OpenLDAPuser',
                throw_error=True)
            if (user == ()):
                return json.dumps(ErrorCodes.admin['invalidUsername'])
            ldap_tools.parse_ldap(user)

            role = self.inst.get_obj(
                'cid', roleId, objectClass='OpenLDAProle', throw_error=True)
            if (roleId not in user['authorizedRoleIds'] and role == ()):
                # If the role does not exist AND the user isn't 'authorized' for it,
                #  return error.
                # If the user is not authorized for a real role, return error.
                # If the user is authorized for a nonexistant role, the admin
                #  may be trying to clean up an error
                return json.dumps(ErrorCodes.admin['invalidRoleId'])
            elif (roleId not in user['authorizedRoleIds']):
                return json.dumps(ErrorCodes.admin['userNotAlreadyAuthorized'])
            ldap_tools.parse_ldap(role)

            virtues = self.inst.get_objs_of_type('OpenLDAPvirtue')
            for v in virtues:
                ldap_tools.parse_ldap(v[1])

                if (v[1]['username'] == username and v[1]['roleId'] == roleId):
                    # Todo: Check if the user is logged on
                    return json.dumps(ErrorCodes.admin['userUsingVirtue'])

            for r in user['authorizedRoleIds']:
                if (r == roleId):
                    user['authorizedRoleIds'].remove(r)
                    del r

            ldap_user = ldap_tools.to_ldap(user, 'OpenLDAPuser')

            self.inst.modify_obj(
                'cusername',
                username,
                ldap_user,
                objectClass='OpenLDAPuser',
                throw_error=True)

            return json.dumps(ErrorCodes.admin['success'])

        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    # Create a virtue for the specified role, but do not launch it yet
    def virtue_create(self, username, roleId, use_nfs=True):

        try:
            user = None
            role = None
            resources = []
            virtue_dict = {}

            user = self.inst.get_obj('cusername', username, 'OpenLDAPuser')
            if (user == None or user == ()):
                return json.dumps(ErrorCodes.admin['invalidUsername'])
            ldap_tools.parse_ldap(user)

            role = self.inst.get_obj('cid', roleId, 'OpenLDAProle', True)
            if (role == ()):
                return json.dumps(ErrorCodes.admin['invalidRoleId'])
            ldap_tools.parse_ldap(role)

            if (roleId not in user['authorizedRoleIds']):
                return json.dumps(ErrorCodes.admin['userNotAlreadyAuthorized'])

            # TODO: If role is still CREATING or FAILED, return error

            virtue = None
            curr_virtues = self.inst.get_objs_of_type('OpenLDAPvirtue')
            for v in curr_virtues:
                ldap_tools.parse_ldap(v[1])
                if (v[1]['username'] == username
                      and v[1]['roleId'] == roleId):
                    return json.dumps(
                        ErrorCodes.user['virtueAlreadyExistsForRole'])

            for rid in role['startingResourceIds']:

                resource = self.inst.get_obj('cid', rid, 'OpenLDAPresource',
                                             True)
                if (resource == ()):
                    continue
                ldap_tools.parse_ldap(resource)

                resources.append(resource)

            virtue_id = 'Virtue_{0}_{1}'.format(role['name'], int(time.time()))

            thr = CreateVirtueThread(self.inst.email, self.inst.password,
                                     role['id'], username, virtue_id, role=role)

            if (use_nfs):
                thr.start()
            else:
                virtue = {
                    'id': virtue_id,
                    'username': username,
                    'roleId': roleId,
                    'applicationIds': [],
                    'resourceIds': role['startingResourceIds'],
                    'transducerIds': role['startingTransducerIds'],
                    'state': 'STOPPED',
                    'ipAddress': 'NULL'
                }
                ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
                self.inst.add_obj(ldap_virtue, 'virtues', 'cid')

            # Return the whole thing
            # return json.dumps( virtue )

            # Return a json of the id and ip address
            return json.dumps({
                'ipAddress': 'NULL',
                'id': virtue_id
            })

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Destroy the specified stopped virtue
    def virtue_destroy(self, virtueId, use_nfs=True):

        try:
            virtue = self.inst.get_obj('cid', virtueId, 'OpenLDAPvirtue', True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.admin['invalidId'])
            ldap_tools.parse_ldap(virtue)

            #if (virtue['username'] != username):
            #    return json.dumps(ErrorCodes.admin['userNotAuthorized'])

            if (virtue['state'] != 'STOPPED'):
                return json.dumps(ErrorCodes.user['virtueNotStopped'])

            try:
                if (use_nfs):
                    subprocess.check_call(
                        ['sudo', 'rm',
                         '/mnt/efs/images/provisioned_virtues/' +
                         virtue['id'] + '.img'])
                self.inst.del_obj('cid', virtue['id'], throw_error=True)
            except:
                print('Error while deleting {0}:\n{1}'.format(
                    virtue['id'], traceback.format_exc()))
                return json.dumps(ErrorCodes.user['serverDestroyError'])

            self.rdb_manager.destroy_virtue(virtue['id'])

            return json.dumps(ErrorCodes.admin['success'])

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])


    def valor_create(self):

        try:

            valor_id = self.valor_api.valor_create()

            return json.dumps({'valor_id' : valor_id})

        except:

            print('Error:\n{0}'.format(traceback.format_exc()))

            return json.dumps(ErrorCodes.user['unspecifiedError'])


    def valor_launch(self, valor_id):

        try:

            valor_id = self.valor_api.valor_launch(valor_id)

            return json.dumps({'valor_id' : valor_id})

        except:

            print('Error:\n{0}'.format(traceback.format_exc()))

            return json.dumps(ErrorCodes.user['unspecifiedError'])


    def valor_stop(self, valor_id):

        try:

            valor_id = self.valor_api.valor_stop(valor_id)

            return json.dumps({'valor_id' : valor_id})

        except:

            print('Error:\n{0}'.format(traceback.format_exc()))

            return json.dumps(ErrorCodes.user['unspecifiedError'])


    def valor_destroy(self, valor_id):

        try:

            valor_id = self.valor_api.valor_destroy(valor_id)

            return json.dumps({'valor_id' : valor_id})

        except:

            print('Error:\n{0}'.format(traceback.format_exc()))

            return json.dumps(ErrorCodes.user['unspecifiedError'])


    def valor_list(self):

        try:

            valors = self.valor_api.valor_list()

            return json.dumps(valors)

        except:

            print('Error:\n{0}'.format(traceback.format_exc()))

            return json.dumps(ErrorCodes.user['unspecifiedError'])


    def valor_create_pool(self, number_of_valors):

        try:

            valor_ids = self.valor_api.valor_create_pool(number_of_valors)

            return json.dumps({'valor_ids' : valor_ids})

        except:

            print('Error:\n{0}'.format(traceback.format_exc()))

            return json.dumps(ErrorCodes.user['unspecifiedError'])


    def valor_migrate_virtue(self, virtue_id, destination_valor_id):

        try:

            valor_id = self.valor_api.valor_migrate_virtue(
                virtue_id,
                destination_valor_id)

            return json.dumps({'valor_id' : valor_id})

        except:

            print('Error:\n{0}'.format(traceback.format_exc()))

            return json.dumps(ErrorCodes.user['unspecifiedError'])


    def galahad_get_id(self):

        try:

            instance_data = AWS.get_instance_info()
            return json.dumps(instance_data['instance-id'])

        except Exception as e:

            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])


    def application_add(self, application):

        try:

            if (set(application.keys()) != set(['id', 'name', 'version', 'os'])
                and set(application.keys()) != set(
                    ['id', 'name', 'version', 'os', 'port'])):
                return json.dumps(ErrorCodes.admin['invalidFormat'])

            for v in application.values():
                if (not isinstance(v), basestring):
                    return json.dumps(ErrorCodes.admin['invalidFormat'])

            if (application['os'] != 'LINUX' and application['os'] != 'WINDOWS'):
                return json.dumps(ErrorCodes.admin['invalidFormat'])

            if (self.inst.get_obj('cid', application['id'], throw_error=True) != ()):
                return json.dumps(ErrorCodes.admin['invalidId'])

            ecr_auth_json = subprocess.check_output([
                'aws', 'ecr', 'get-authorization-token',
                '--output', 'json',
                '--region', 'us-east-2'])

            ecr_auth = json.loads(ecr_auth_json.decode())

            docker_registry = ecr_auth['authorizationData'][0]['proxyEndpoint']
            docker_token = ecr_auth['authorizationData'][0]['authorizationToken']

            # Since the user is only adding the app, not creating it, make sure
            # the image is already in the docker repo.
            response = requests.get(
                '{0}/v2/starlab-virtue/tags/list'.format(docker_registry),
                headers={'Authorization': 'Basic ' + docker_token})

            if ('virtue-' + application['id'] not in response.json()['tags']):
                return json.dumps(ErrorCodes.admin['imageNotFound'])

            ldap_app = ldap_tools.to_ldap(application, 'OpenLDAPapplication')
            ret = self.inst.add_obj(ldap_app, 'virtues', 'cid')
            assert ret == 0

            return json.dumps(ErrorCodes.admin['success'])

        except Exception as e:

            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])


    def virtue_introspect_start(self, virtue_id, interval=None, modules=None):
        try:
            self.rdb_manager.introspect_virtue_start(virtue_id, interval, modules)
            return json.dumps({'virtue_id': virtue_id})
        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])


    def virtue_introspect_stop(self, virtue_id):
        try:
            self.rdb_manager.introspect_virtue_stop(virtue_id)
            return json.dumps({'virtue_id': virtue_id})
        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])
