# Copyright (c) 2019 by Star Lab Corp.

import json
import os
import subprocess
import sys
import time

import requests

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(file_path))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)

from website.ldaplookup import LDAP
from website.apiendpoint import EndPoint
from website.apiendpoint_admin import EndPoint_Admin
from website.services.errorcodes import ErrorCodes

sys.path.insert(0, base_excalibur_dir + '/cli')
from sso_login import sso_tool

EXCALIBUR_HOSTNAME = 'excalibur.galahad.com'

# Time after which we will declare an error
TIMEOUT = 1200


def create_new_role(role_name, unity_img_name=None):
    admin_api, user_api = create_apiendpoints()

    role_data = {'name': role_name, 'version': '1.0', 'applicationIds': ['firefox'],
        'startingResourceIds': [],
        'startingTransducerIds': ['path_mkdir', 'bprm_set_creds', 'task_create',
                                  'task_alloc', 'inode_create', 'socket_connect',
                                  'socket_bind', 'socket_accept', 'socket_listen',
                                  'create_process', 'process_start', 'process_died',
                                  'srv_create_proc', 'open_fd'],
        'networkRules': []}

    if (unity_img_name != None):
        new_role = json.loads(
            admin_api.role_create(role_data, unity_img_name=unity_img_name))
    else:
        new_role = json.loads(admin_api.role_create(role_data))

    if new_role in ErrorCodes.admin.values():
        raise Exception('Error creating new role - {}'.format(new_role))

    print('New Role is {}'.format(new_role))

    time.sleep(5)

    # Wait for role to create
    time_elapsed = 0
    role = role_get(admin_api, new_role['id'])
    while (role['state'] == 'CREATING'):
        time.sleep(5)
        role = role_get(admin_api, new_role['id'])
        time_elapsed = time_elapsed + 5
        if (time_elapsed >= TIMEOUT):
            raise Exception(
                'Timed out waiting for role [{}] to be created in [{}] seconds'.format(
                    role['name'], time_elapsed))

    print('New Role <{0}> created in [{1}] seconds'.format(role, time_elapsed))

    return role


def create_new_virtue(user, role_id):
    # Get API endpoints
    admin_api, user_api = create_apiendpoints()

    role = role_get(admin_api, role_id)

    # Check if the role exists
    if not role:
        raise Exception(
            'Failed to retrieve role [{0}] from the role ID [{1}]'.format(role, role_id))

    # user_role_authorize(). It's ok if the user is already authorized.
    admin_api.user_role_authorize(user, role['id'])

    # delete existing virtue if any
    user_virtue_list = json.loads(admin_api.user_virtue_list(user))
    for virtue in user_virtue_list:
        if (virtue['roleId'] == role['id']):
            user_api.virtue_stop(user, virtue['id'])  # It's ok if it's already stopped
            res = json.loads(admin_api.virtue_destroy(virtue['id']))
            if res != ErrorCodes.admin['success']:
                raise Exception(
                    'Failed to destroy virtue [{0}] with error [{1}]'.format(virtue['id'],
                                                                             res))

    # virtue_create()
    new_virtue = json.loads(admin_api.virtue_create(user, role['id']))
    if set(new_virtue.keys()) != set(['id', 'ipAddress']):
        raise Exception(
            'Error in return value for virtue_create [{}]'.format(set(new_virtue.keys())))

    print('New Virtue is {}'.format(new_virtue))

    time.sleep(5)

    # Wait for virtue to create
    time_elapsed = 0
    virtue = virtue_get(admin_api, user, new_virtue['id'])
    while (virtue['state'] == 'CREATING'):
        time.sleep(5)
        virtue = virtue_get(admin_api, user, new_virtue['id'])
        time_elapsed = time_elapsed + 5
        if (time_elapsed >= TIMEOUT):
            raise Exception(
                'Timed out waiting for virtue [{}] to be created in [{}] seconds'.format(
                    virtue['id'], time_elapsed))

    print('New Virtue <{0}> created in [{1}] seconds'.format(virtue, time_elapsed))

    if virtue['state'] != 'STOPPED':
        raise Exception('Virtue is not in stopped state [{}]'.format(virtue['state']))

    # virtue_launch
    user_api.virtue_launch(user, new_virtue['id'])

    return json.loads(user_api.virtue_get(user, new_virtue['id']))


def role_get(admin_api, role_id):
    roles = json.loads(admin_api.role_list())

    for role in roles:
        if role_id == role['id']:
            return role

    return


def virtue_get(admin_api, user, virtue_id):
    virtues = json.loads(admin_api.user_virtue_list(user))

    for virtue in virtues:
        if virtue_id == virtue['id']:
            return virtue

    return


def create_apiendpoints():
    inst = LDAP('', '')
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s(dn, 'Test123!')

    admin_api = EndPoint_Admin('slapd', 'Test123!')
    admin_api.inst = inst

    user_api = EndPoint('slapd', 'Test123!')
    user_api.inst = inst

    return admin_api, user_api


def create_session():
    with open('test_config.json', 'r') as infile:
        settings = json.load(infile)

    excalibur_url = EXCALIBUR_HOSTNAME + ':' + settings['port']

    redirect = settings['redirect'].format(excalibur_url)

    sso = sso_tool(excalibur_url)
    res = sso.login(settings['user'], settings['password'])
    if not res:
        raise Exception('Failed to login [{}]'.format(res))

    client_id = sso.get_app_client_id(settings['app_name'])
    if (client_id == None):
        client_id = sso.create_app(settings['app_name'], redirect)
        if not client_id:
            raise Exception('Failed to create oauth app [{}]'.format(client_id))

    code = sso.get_oauth_code(client_id, redirect)
    if not code:
        raise Exception('Failed to get oauth code [{}]'.format(code))

    token = sso.get_oauth_token(client_id, code, redirect)
    if not 'access_token' in token:
        raise Exception('Failed to get access token from oauth token [{}]'.format(token))

    session = requests.Session()
    session.headers = {'Authorization': 'Bearer {0}'.format(token['access_token'])}
    session.verify = settings['verify']

    admin_url = 'https://{0}/virtue/admin'.format(excalibur_url)

    security_url = 'https://{0}/virtue/security'.format(excalibur_url)

    user_url = 'https://{0}/virtue/user'.format(excalibur_url)

    return session, admin_url, security_url, user_url


def cleanup_virtue(user, virtue_id):
    admin_api, user_api = create_apiendpoints()

    user_api.virtue_stop(user, virtue_id)

    res = json.loads(admin_api.virtue_destroy(virtue_id))
    if res != ErrorCodes.admin['success']:
        raise Exception(
            'Failed to destroy virtue [{0}] with error [{1}]'.format(virtue_id, res))


def cleanup_role(user, role_id):
    admin_api, user_api = create_apiendpoints()

    admin_api.user_role_unauthorize(user, role_id)

    # Delete the role ID from LDAP
    inst = LDAP('', '')
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s(dn, 'Test123!')

    inst.del_obj('cid', role_id, objectClass='OpenLDAProle', throw_error=True)

    # Delete the role img file
    subprocess.check_call(
        ['sudo', 'rm', '/mnt/efs/images/non_provisioned_virtues/' + role_id + '.img'])
