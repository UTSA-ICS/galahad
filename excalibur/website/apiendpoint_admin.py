# Copyright (c) 2019 by Star Lab Corp.

import copy
import json
import os
import subprocess
import time
import traceback

import requests

from apiendpoint import EndPoint
from controller import CreateVirtueThread, AssembleRoleThread
from create_ldap_users import update_ldap_users_from_ad
from ldaplookup import LDAP
from services.errorcodes import ErrorCodes
from valor import ValorAPI, RethinkDbManager
from . import ldap_tools

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

    def resource_create(self, resource):
        try:
            resource_keys = [
                'credentials',
                'type',
                'unc'
            ]
            if (set(resource.keys()) != set(resource_keys)
                    and set(resource.keys()) != set(resource_keys + ['id'])):
                return json.dumps(ErrorCodes.admin['invalidFormat'])
            if (not isinstance(resource['credentials'], basestring)
                    or not isinstance(resource['type'], basestring)
                    or not isinstance(resource['unc'], basestring)):
                return json.dumps(ErrorCodes.admin['invalidFormat'])
            resource['id'] = 'Resource_{}_{}'.format(resource['type'], int(time.time()))
            ldap_resource = ldap_tools.to_ldap(resource, 'OpenLDAPresource')
            self.inst.add_obj(ldap_resource, 'resources', 'cid', throw_error=True)

            return json.dumps(resource)
        except Exception as e:
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def resource_destroy(self, resourceId):
        try:
            resource = self.inst.get_obj('cid', resourceId, 'OpenLDAPresource', True)
            if (resource == ()):
                return json.dumps(ErrorCodes.admin['invalidId'])
            ldap_tools.parse_ldap(resource)

            # KL --- add check if in use
            ldap_virtues = self.inst.get_objs_of_type('OpenLDAPvirtue')
            virtues = ldap_tools.parse_ldap_list(ldap_virtues)

            if any(resourceId in virtue['resourceIds'] for virtue in virtues):
                return json.dumps(ErrorCodes.admin['virtueUsingResource'])

            self.inst.del_obj('cid', resource['id'], throw_error=True)
        except:
            print('Error while deleting {}:\n{}'.format(
                resource['id'], traceback.format_exc()))
            return json.dumps(ErrorCodes.user['serverDestroyError'])

        return json.dumps(ErrorCodes.admin['success'])

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

            # if (virtue['state'] == 'DELETING'):
            #    return json.dumps(ErrorCodes.admin['invalidVirtueState'])
            if (virtue['state'] != 'STOPPED'):
                return json.dumps(ErrorCodes.admin['invalidVirtueState'])

            if (resourceId in virtue['resourceIds']):
                return json.dumps(ErrorCodes.admin['cantAttach'])

            virtue['resourceIds'].append(resourceId)
            self.inst.modify_obj('cid', virtue['id'],
                ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue'),
                objectClass='OpenLDAPvirtue',
                throw_error=True)

            # return json.dumps(ErrorCodes.admin['notImplemented'])
            return json.dumps(ErrorCodes.admin['success'])

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

            if (virtue['state'] != 'STOPPED'):
                return json.dumps(ErrorCodes.admin['invalidVirtueState'])

            virtue['resourceIds'].remove(resourceId)
            self.inst.modify_obj('cid', virtue['id'],
                ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue'),
                objectClass='OpenLDAPvirtue',
                throw_error=True)

            # return json.dumps(ErrorCodes.admin['notImplemented'])
            return json.dumps(ErrorCodes.admin['success'])
        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def role_create(self, role, use_ssh=True, unity_img_name=None):

        try:
            role_keys = [
                'name',
                'version',
                'applicationIds',
                'startingResourceIds',
                'startingTransducerIds',
                'networkRules'
            ]
            if (set(role.keys()) != set(role_keys)
                    and set(role.keys()) != set(role_keys + ['id'])):
                return json.dumps(ErrorCodes.admin['invalidFormat'])

            if (not isinstance(role['name'], basestring)
                    or not isinstance(role['version'], basestring)
                    or type(role['applicationIds']) != list
                    or type(role['startingResourceIds']) != list
                    or type(role['networkRules']) != list
                    or type(role['startingTransducerIds']) != list):
                return json.dumps(ErrorCodes.admin['invalidFormat'])

            if not role['applicationIds']:
                return json.dumps(ErrorCodes.admin['NoApplicationId'])

            default_unity_size = 3  # Measured in GB.

            for a in role['applicationIds']:
                app_test = self.inst.get_obj(
                    'cid',
                    a,
                    objectClass='OpenLDAPapplication',
                    throw_error=True)
                if (app_test == ()):
                    return json.dumps(ErrorCodes.admin['invalidApplicationId'])

                ldap_tools.parse_ldap(app_test)

                if (app_test['os'] == 'WINDOWS'):
                    if (app_test['name'].startswith('Microsoft Office')):
                        default_unity_size = default_unity_size + 7
                    else:
                        default_unity_size = default_unity_size + 3
                else:
                    default_unity_size = default_unity_size + 2

            for r in role['startingResourceIds']:
                res_test = self.inst.get_obj(
                    'cid', r, objectClass='OpenLDAPresource', throw_error=True)
                if (res_test == ()):
                    return json.dumps(ErrorCodes.admin['invalidResourceId'])

            ldap_transducers = self.inst.get_objs_of_type('OpenLDAPtransducer')
            assert ldap_transducers != None

            all_transducers = ldap_tools.parse_ldap_list(ldap_transducers)

            for t in role['startingTransducerIds']:
                if (t not in [tr['id'] for tr in all_transducers]):
                    return json.dumps(ErrorCodes.admin['invalidTransducerId'])

            new_role = copy.deepcopy(role)

            for t in all_transducers:
                if (t['startEnabled'] and
                    t['id'] not in role['startingTransducerIds']):
                    new_role['startingTransducerIds'].append(t['id'])

            new_role['id'] = '{0}{1}'.format(new_role['name'].lower().replace(' ', '_'), int(time.time()))

            if (unity_img_name == None):

                closest_fit = 0
                for img in os.listdir('/mnt/efs/images/unities'):
                    img_size = int(img.replace('GB.img', ''))
                    if (img_size >= default_unity_size
                        and (closest_fit == 0 or closest_fit > img_size)):
                        closest_fit = img_size

                if (closest_fit != 0):
                    unity_img_name = '{}GB'.format(closest_fit)
                else:
                    return json.dumps({
                        'status': 'failed',
                        'result': [
                            17, ('Could not automatically find a usable unity'
                                 ' for this role. Please specify a unity'
                                 ' image.')
                        ]})

            if ((unity_img_name + '.img') not in os.listdir(
                    '/mnt/efs/images/unities')):
                return json.dumps({
                    'status': 'failed',
                    'result': [
                        17, ('Could not find a unity with the name'
                             ' ({})').format(unity_img_name)
                    ]})

            try:
                # Call a controller thread to create and assemble the new image
                thr = AssembleRoleThread(self.inst.email, self.inst.password,
                                         new_role, unity_img_name,
                                         use_ssh=use_ssh)
            except AssertionError:
                return json.dumps(ErrorCodes.admin['storageError'])
            thr.start()

            return json.dumps({'id': new_role['id'], 'name': new_role['name']})

        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    # Destroy the specified role
    def role_destroy(self, roleId, use_nfs=True):

        try:
            role = self.inst.get_obj('cid', roleId, 'OpenLDAProle', True)
            if (role == ()):
                return json.dumps(ErrorCodes.admin['invalidId'])
            ldap_tools.parse_ldap(role)

            # Check if any virtues exist with given role
            virtues = self.inst.get_objs_of_type('OpenLDAPvirtue')
            for virtue in virtues:
                ldap_tools.parse_ldap(virtue[1])
                if (virtue[1]['roleId'] == roleId):
                    # A Virtue exists for this role - Unable to destroy role
                    virtueUsingRoleError = []
                    virtueUsingRoleError.append({'Virtue using the '
                                                 'specified role exists':
                                                     virtue[1]['id']})
                    virtueUsingRoleError.append(
                        ErrorCodes.admin['virtueUsingRole'])
                    return json.dumps(virtueUsingRoleError)

            # Check if any user is authorized for the given role
            users = self.inst.get_objs_of_type('OpenLDAPuser')
            for user in users:
                ldap_tools.parse_ldap(user[1])
                if (roleId in user[1]['authorizedRoleIds']):
                    # A User exists with this role authorized - Unable to
                    # destroy role
                    userUsingRoleError = []
                    userUsingRoleError.append({'User authorized for the '
                                               'specified role exists':
                                               user[1]['username']})
                    userUsingRoleError.append(
                        ErrorCodes.admin['userUsingRole'])
                    return json.dumps(userUsingRoleError)

            try:
                self.inst.del_obj('cid', roleId, throw_error=True)
                if (use_nfs):
                    subprocess.check_call(
                        ['sudo', 'rm',
                         '/mnt/efs/images/non_provisioned_virtues/' +
                         role['id'] + '.img'])

                    # Delete the Standby virtue role image files
                    files = os.listdir('/mnt/efs/images/provisioned_virtues/')
                    standby_files = (file for file in files if role['id'] +
                                     '_STANDBY_VIRTUE_' in file)
                    for standby_file in standby_files:
                        subprocess.check_call(
                            ['sudo', 'rm',
                             '/mnt/efs/images/provisioned_virtues/' +
                             standby_file])
            except:
                print('Error while deleting {0}:\n{1}'.format(
                    role['id'], traceback.format_exc()))
                return json.dumps(ErrorCodes.admin['roleDestroyError'])

            return json.dumps(ErrorCodes.admin['success'])

        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

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
            # Check AD and update user list in ldap if required
            update_ldap_users_from_ad()

            ldap_users = self.inst.get_objs_of_type('OpenLDAPuser')
            assert ldap_users != None

            users = ldap_tools.parse_ldap_list(ldap_users)

            return json.dumps(users)

        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def user_get(self, username):

        try:
            # Check AD and update user list in ldap if required
            update_ldap_users_from_ad()

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

        try:
            # Check AD and update user list in ldap if required
            update_ldap_users_from_ad()

            user = self.inst.get_obj(
                'cusername', username, objectClass='OpenLDAPuser')
            if (user == ()):
                return json.dumps(ErrorCodes.admin['invalidUsername'])
            elif (user == None):
                return json.dumps(ErrorCodes.admin['unspecifiedError'])

            ep = EndPoint(self.inst.email, self.inst.password)

            return ep.user_virtue_list(username)

        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def user_role_authorize(self, username, roleId):

        try:
            # Check AD and update user list in ldap if required
            update_ldap_users_from_ad()

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
                    # The user is authorized for a nonexistent role...
                    # Remove it from their list?
                    pass
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
                # If the role does not exist AND the user isn't 'authorized'
                # for it, return error. If the user is not authorized for a
                # real role, return error. If the user is authorized for a
                # nonexistent role, the admin may be trying to clean up an error
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

            if (role.get('state', 'CREATED') != 'CREATED'):
                return json.dumps(ErrorCodes.admin['invalidRoleState'])

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

            virtue_id = 'Virtue_{0}_{1}'.format(
                role['name'].lower().replace(' ', '_'),
                int(time.time()))

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
                    'networkRules': role['networkRules'],
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

    def virtue_reload_state(self, virtueId):

        try:
            virtue = self.inst.get_obj('cid', virtueId, 'OpenLDAPvirtue', True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.user['invalidId'])
            ldap_tools.parse_ldap(virtue)

            updated_virtue = copy.deepcopy(virtue)

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

    def valor_create(self):

        try:

            valor_id = self.valor_api.valor_create()

            return json.dumps({'valor_id': valor_id})

        except:

            print('Error:\n{0}'.format(traceback.format_exc()))

            return json.dumps(ErrorCodes.user['unspecifiedError'])

    def valor_launch(self, valor_id):

        try:

            valor_id = self.valor_api.valor_launch(valor_id)

            return json.dumps({'valor_id': valor_id})

        except:

            print('Error:\n{0}'.format(traceback.format_exc()))

            return json.dumps(ErrorCodes.user['unspecifiedError'])

    def valor_stop(self, valor_id):

        try:

            valor_id = self.valor_api.valor_stop(valor_id)

            return json.dumps({'valor_id': valor_id})

        except Exception as exception:

            print('Error:\n{0}'.format(traceback.format_exc()))

            # Virtue/s exists on this valor - Unable to stop valor
            return json.dumps({'status': 'failed', 'result': [11, exception.message]})

    def valor_destroy(self, valor_id):

        try:

            valor_id = self.valor_api.valor_destroy(valor_id)

            return json.dumps({'valor_id': valor_id})

        except Exception as exception:

            print('Error:\n{0}'.format(traceback.format_exc()))

            # Virtue/s exists on this valor - Unable to destroy valor
            return json.dumps(
                {'status': 'failed', 'result': [11, exception.message]})

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

            return json.dumps({'valor_ids': valor_ids})

        except:

            print('Error:\n{0}'.format(traceback.format_exc()))

            return json.dumps(ErrorCodes.user['unspecifiedError'])

    def valor_migrate_virtue(self, virtue_id, destination_valor_id):

        try:

            valor_id = self.valor_api.valor_migrate_virtue(
                virtue_id,
                destination_valor_id)

            return json.dumps({'valor_id': valor_id})

        except Exception as exception:

            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(
                {'status': 'failed', 'result': [11, exception.message]})

    def galahad_get_id(self):

        try:

            instance_data = AWS.get_instance_info()
            return json.dumps(instance_data['instance-id'])

        except Exception as e:

            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def application_add(self, application):

        try:

            app = copy.copy(application)

            if (set(app.keys()) != set(['id', 'name', 'version', 'os'])
                and set(app.keys()) != set(
                    ['id', 'name', 'version', 'os', 'port'])):
                return json.dumps(ErrorCodes.admin['invalidFormat'])

            if (isinstance(app.get('port'), basestring)):
                app['port'] = int(app['port'])

            if (not isinstance(app['id'], basestring)
                or not isinstance(app['name'], basestring)
                or not isinstance(app['version'], basestring)
                or type(app.get('port', 0)) != int):
                return json.dumps(ErrorCodes.admin['invalidFormat'])

            if (app['os'] != 'LINUX' and app['os'] != 'WINDOWS'):
                return json.dumps(ErrorCodes.admin['invalidFormat'])

            if (self.inst.get_obj('cid', app['id'], throw_error=True) != ()):
                return json.dumps(ErrorCodes.admin['invalidId'])

            ecr_auth_json = subprocess.check_output([
                'aws', 'ecr', 'get-authorization-token',
                '--registry-ids', '703915126451',
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

            if ('virtue-' + app['id'] not in response.json()['tags']):
                return json.dumps(ErrorCodes.admin['imageNotFound'])

            ldap_app = ldap_tools.to_ldap(app, 'OpenLDAPapplication')
            ret = self.inst.add_obj(ldap_app, 'virtues', 'cid')
            assert ret == 0

            return json.dumps(ErrorCodes.admin['success'])

        except Exception as e:

            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])

    def auto_migration_start(self, migration_interval=None):
        try:
            self.valor_api.auto_migration_start(migration_interval)
            return json.dumps(ErrorCodes.admin['success'])
        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    def auto_migration_stop(self):
        try:
            self.valor_api.auto_migration_stop()
            return json.dumps(ErrorCodes.admin['success'])
        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    def auto_migration_status(self):
        try:
            status, interval = self.valor_api.auto_migration_status()
            if status:
                migration_status = 'ON'
                return json.dumps({'auto_migration_status': migration_status,
                                   'auto_migration_interval': interval})
            else:
                migration_status = 'OFF'
                return json.dumps({'auto_migration_status': migration_status})
        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

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

    def virtue_introspect_start_all(self, interval=None, modules=None):
        try:
            virtues_raw = self.inst.get_objs_of_type('OpenLDAPvirtue')
            if (virtues_raw == None):
                return json.dumps(ErrorCodes.user['unspecifiedError'])

            for virtue in virtues_raw:
                ldap_tools.parse_ldap(virtue[1])
                virtue_running = (virtue[1]['state'] == 'RUNNING')
                if virtue_running:
                    self.rdb_manager.introspect_virtue_start(virtue[1]['id'], interval, modules)

            return json.dumps(ErrorCodes.admin['success'])
        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    def virtue_introspect_stop_all(self):
        try:
            virtues_raw = self.inst.get_objs_of_type('OpenLDAPvirtue')
            if (virtues_raw == None):
                return json.dumps(ErrorCodes.user['unspecifiedError'])

            for virtue in virtues_raw:
                ldap_tools.parse_ldap(virtue[1])
                virtue_running = (virtue[1]['state'] == 'RUNNING')
                if virtue_running:
                    self.rdb_manager.introspect_virtue_stop(virtue[1]['id'])

            return json.dumps(ErrorCodes.admin['success'])
        except:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    def _set_introspection_ldap(self, virtueId, isEnabled):
        introsection_id = 'introspection'
        virtue = self.inst.get_obj('cid', virtueId,
                                   'OpenLDAPvirtue', True)
        if virtue is None or virtue == ():
            return json.dumps(ErrorCodes.admin['invalidVirtueId'])

        ldap_tools.parse_ldap(virtue)

        new_t_list = json.loads(virtue['transducerIds'])

        if isEnabled:
            if introsection_id not in new_t_list:
                new_t_list.append(introsection_id)
        else:
            if introsection_id in new_t_list:
                new_t_list.remove(introsection_id)

        virtue['transducerIds'] = json.dumps(new_t_list)
        ret = self.inst.modify_obj('cid', virtueId, ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue'),
                                   'OpenLDAPvirtue', True)
        if ret != 0:
            return json.dumps(ErrorCodes.user['unspecifiedError'])

        return json.dumps(ErrorCodes.admin['success'])

    def _set_introspection_role(self, isEnabled):
        introspection_id = 'introspection'
        try:
            ldap_roles = self.inst.get_objs_of_type('OpenLDAProle')
            assert ldap_roles != None

            roles = ldap_tools.parse_ldap_list(ldap_roles)

            for role in roles:
                print(role)
                print(role['startingTransducerIds'])
                new_t_list = role['startingTransducerIds']

                if isEnabled:
                    if introspection_id not in new_t_list:
                        new_t_list.append(introspection_id)
                else:
                    if introspection_id in new_t_list:
                        new_t_list.remove(introspection_id)

                role['startingTransducerIds'] = new_t_list
                ret = self.inst.modify_obj('cid', role['id'], ldap_tools.to_ldap(role, 'OpenLDAProle'),
                                           'OpenLDAProle', True)
                if ret != 0:
                    return json.dumps(ErrorCodes.user['unspecifiedError'])

            return True

        except Exception as e:
            print('Error:\n{0}'.format(traceback.format_exc()))
            return json.dumps(ErrorCodes.admin['unspecifiedError'])
