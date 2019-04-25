#!/usr/bin/python

# Copyright (c) 2019 by Star Lab Corp.

import json
import os
import sys
import time
import subprocess

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(file_path)) + '/../excalibur'
sys.path.insert(0, base_excalibur_dir)
from website import ldap_tools
from website.ldaplookup import LDAP
from website.apiendpoint_admin import EndPoint_Admin
from website.services.errorcodes import ErrorCodes


def setup_module():

    global inst
    global ep
    global test_role_id
    global test_virtue_id

    inst = LDAP('', '')
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s(dn, 'Test123!')

    ep = EndPoint_Admin('slapd', 'Test123!')
    ep.inst = inst

    role = {
        'id': 'admintestrole0',
        'name': 'AdminTestRole',
        'version': '1.0',
        'applicationIds': ['firefox'],
        'startingResourceIds': [],
        'startingTransducerIds': [],
        'networkRules': []
    }

    ldap_role = ldap_tools.to_ldap(role, 'OpenLDAProle')
    inst.add_obj(ldap_role, 'roles', 'cid', throw_error=True)

    user = inst.get_obj(
        'cusername', 'slapd', objectClass='OpenLDAPuser', throw_error=True)
    ldap_tools.parse_ldap(user)

    if ('admintestrole0' not in user['authorizedRoleIds']):
        user['authorizedRoleIds'].append('admintestrole0')
        ldap_user = ldap_tools.to_ldap(user, 'OpenLDAPuser')
        inst.modify_obj(
            'cusername',
            'slapd',
            ldap_user,
            objectClass='OpenLDAPuser',
            throw_error=True)

    # set to satisfy pytest when listing tests
    test_role_id = None
    test_virtue_id = None

def teardown_module():

    inst.del_obj(
        'cid', 'admintestrole0', objectClass='OpenLDAProle', throw_error=True)

    inst.del_obj(
        'cid', 'admintestvirtue0', objectClass='OpenLDAPvirtue', throw_error=True)

    if os.path.exists(('/mnt/efs/images/non_provisioned_virtues/'
                       'admintestrole0.img')):
        subprocess.check_call(['sudo', 'rm',
                               ('/mnt/efs/images/non_provisioned_virtues/'
                                'admintestrole0.img')])

    if os.path.exists(('/mnt/efs/images/provisioned_virtues/'
                       'admintestvirtue0.img')):
        subprocess.check_call(['sudo', 'rm',
                               ('/mnt/efs/images/provisioned_virtues/'
                                'admintestvirtue0.img')])

    if test_role_id is not None:
        inst.del_obj('cid', test_role_id,
                     objectClass='OpenLDAProle', throw_error=True)
        if os.path.exists(('/mnt/efs/images/non_provisioned_virtues/'
                           '{0}.img').format(test_role_id)):
            subprocess.check_call(['sudo', 'rm',
                                   ('/mnt/efs/images/non_provisioned_virtues/'
                                    '{0}.img').format(test_role_id)])

    if test_virtue_id is not None:
        inst.del_obj('cid', test_virtue_id,
                     objectClass='OpenLDAPvirtue', throw_error=True)
        if os.path.exists(('/mnt/efs/images/provisioned_virtues/'
                           '{0}.img').format(test_virtue_id)):
            subprocess.check_call(['sudo', 'rm',
                                   ('/mnt/efs/images/provisioned_virtues/'
                                    '{0}.img').format(test_virtue_id)])


    user = inst.get_obj(
        'cusername', 'slapd', objectClass='OpenLDAPuser', throw_error=True)
    ldap_tools.parse_ldap(user)

    user['authorizedRoleIds'].remove('admintestrole0')
    ldap_user = ldap_tools.to_ldap(user, 'OpenLDAPuser')
    inst.modify_obj(
        'cusername',
        'slapd',
        ldap_user,
        objectClass='OpenLDAPuser',
        throw_error=True)


def test_application_calls():
    # application_list
    app_list = ep.application_list()

    ldap_app_list = inst.get_objs_of_type('OpenLDAPapplication')
    real_app_list = ldap_tools.parse_ldap_list(ldap_app_list)

    assert json.loads(app_list) == real_app_list


def test_resource_calls():
    # resource_get
    assert json.dumps(
        ErrorCodes.admin['invalidId']) == ep.resource_get('DoesNotExist')

    res = ep.resource_get('fileshare1')

    ldap_res = inst.get_obj(
        'cid', 'fileshare1', objectClass='OpenLDAPresource', throw_error=True)
    assert ldap_res != ()

    ldap_tools.parse_ldap(ldap_res)

    assert res == json.dumps(ldap_res)

    # resource_list
    res_list = ep.resource_list()

    ldap_res_list = inst.get_objs_of_type('OpenLDAPresource')
    real_res_list = ldap_tools.parse_ldap_list(ldap_res_list)

    assert res_list == json.dumps(real_res_list)

    # resource_attach (NotImplemented)
    # resource_detach (NotImplemented)


def test_role_calls():
    # role_create
    good_role = {
        'id': 'NotRelevant',
        'name': 'browsing',
        'version': '1.0',
        'applicationIds': ['firefox', 'thunderbird'],
        'startingResourceIds': ['fileshare1'],
        'startingTransducerIds': [],
        'networkRules': []
    }

    bad_role_1 = {
        'id': 'NotRelevant',
        'version': '1.0',
        'applicationIds': ['firefox', 'thunderbird'],
        'startingResourceIds': ['fileshare1'],
        'startingTransducerIds': [],
        'networkRules': []
    }

    bad_role_2 = {
        'id': 'NotRelevant',
        'name': 'browsing',
        'version': '1.0',
        'applicationIds': "['firefox', 'thunderbird']",
        'startingResourceIds': "['fileshare1']",
        'startingTransducerIds': "[]",
        'networkRules': []
    }

    bad_role_3 = {
        'id': 'NotRelevant',
        'name': 'browsing',
        'version': '1.0',
        'applicationIds': ['firefox', 'thunderbird', 'DoesNotExist'],
        'startingResourceIds': ['fileshare1'],
        'startingTransducerIds': [],
        'networkRules': []
    }

    bad_role_4 = {
        'id': 'NotRelevant',
        'name': 'browsing',
        'version': '1.0',
        'applicationIds': ['firefox', 'thunderbird'],
        'startingResourceIds': ['fileshare1', 'DoesNotExist'],
        'startingTransducerIds': [],
        'networkRules': []
    }

    bad_role_5 = {
        'id': 'NotRelevant',
        'name': 'browsing',
        'version': '1.0',
        'applicationIds': ['firefox', 'thunderbird'],
        'startingResourceIds': ['fileshare1'],
        'startingTransducerIds': ['DoesNotExist'],
        'networkRules': []
    }

    bad_role_6 = {
        'id': 'NotRelevant',
        'name': 'browsing',
        'version': '1.0',
        'applicationIds': [],
        'startingResourceIds': ['fileshare1'],
        'startingTransducerIds': ['DoesNotExist'],
        'networkRules': []
    }

    assert json.dumps(ErrorCodes.admin['invalidFormat']) == ep.role_create(
        bad_role_1, use_ssh=False)
    assert json.dumps(ErrorCodes.admin['invalidFormat']) == ep.role_create(
        bad_role_2, use_ssh=False)

    assert json.dumps(
        ErrorCodes.admin['invalidApplicationId']) == ep.role_create(
            bad_role_3, use_ssh=False)

    assert json.dumps(ErrorCodes.admin['invalidResourceId']) == ep.role_create(
        bad_role_4, use_ssh=False)

    assert json.dumps(
        ErrorCodes.admin['invalidTransducerId']) == ep.role_create(
            bad_role_5, use_ssh=False)

    assert json.dumps(
        ErrorCodes.admin['NoApplicationId']) == ep.role_create(
            bad_role_6, use_ssh=False)

    result_role_json = ep.role_create(good_role, use_ssh=False)

    result_role = json.loads(result_role_json)

    # role create should ignore the ID provided
    assert result_role['id'] != 'NotRelevant'
    assert result_role == {'id': result_role['id'], 'name': good_role['name']}

    good_role['id'] = result_role['id']
    good_role['state'] = 'CREATED'
    good_role['startingTransducerIds'] = [
        'path_mkdir', 'bprm_set_creds', 'task_create', 'task_alloc',
        'inode_create', 'socket_connect', 'socket_bind', 'socket_accept',
        'socket_listen', 'create_process', 'process_start', 'process_died',
        'srv_create_proc', 'open_fd'
    ]

    time.sleep(1)

    ldap_role = inst.get_obj('cid', result_role['id'],
                             objectClass='OpenLDAProle')
    assert ldap_role != ()
    ldap_tools.parse_ldap(ldap_role)

    # TODO: Make sure loops like these don't continue forever.
    while (ldap_role['state'] == 'CREATING'):
        time.sleep(5)
        ldap_role = inst.get_obj('cid', result_role['id'])
        ldap_tools.parse_ldap(ldap_role)

    assert ldap_role == good_role
    assert os.path.exists(('/mnt/efs/images/non_provisioned_virtues/'
                           '{0}.img').format(result_role['id']))

    # This will be used in teardown_module()
    global test_role_id
    test_role_id = result_role['id']

    # role_list
    role_list = ep.role_list()

    ldap_role_list = inst.get_objs_of_type('OpenLDAProle')
    real_role_list = ldap_tools.parse_ldap_list(ldap_role_list)

    assert role_list == json.dumps(real_role_list)

    # user_role_authorize
    assert json.dumps(
        ErrorCodes.admin['invalidUsername']) == ep.user_role_authorize(
            'DoesNotExist', test_role_id)

    assert json.dumps(
        ErrorCodes.admin['invalidRoleId']) == ep.user_role_authorize(
            'slapd', 'DoesNotExist')

    assert ep.user_role_authorize('slapd', test_role_id) == json.dumps(
        ErrorCodes.admin['success'])

    # Make sure LDAP has been updated
    user = inst.get_obj(
        'cusername', 'slapd', objectClass='OpenLDAPuser', throw_error=True)
    ldap_tools.parse_ldap(user)

    assert test_role_id in user['authorizedRoleIds']

    # Try to authorize twice
    assert json.dumps(
        ErrorCodes.admin['userAlreadyAuthorized']) == ep.user_role_authorize(
            'slapd', test_role_id)

    # user_role_unauthorize
    assert json.dumps(
        ErrorCodes.admin['invalidUsername']) == ep.user_role_unauthorize(
            'DoesNotExist', test_role_id)

    assert json.dumps(
        ErrorCodes.admin['invalidRoleId']) == ep.user_role_unauthorize(
            'slapd', 'DoesNotExist')

    # Todo: Check return when user is using a virtue

    assert ep.user_role_unauthorize('slapd', test_role_id) == json.dumps(
        ErrorCodes.admin['success'])

    # Make sure LDAP has been updated
    user = inst.get_obj(
        'cusername', 'slapd', objectClass='OpenLDAPuser', throw_error=True)
    ldap_tools.parse_ldap(user)

    assert test_role_id not in user['authorizedRoleIds']

    # Try to unauthorize twice
    assert json.dumps(ErrorCodes.admin[
        'userNotAlreadyAuthorized']) == ep.user_role_unauthorize(
            'slapd', test_role_id)

    # system_export (NotImplemented)
    # system_import (NotImplemented)
    # test_import_user (NotImplemented)
    # test_import_application (NotImplemented)
    # test_import_role (NotImplemented)


def test_user_calls():
    # user_list
    user_list = ep.user_list()

    ldap_user_list = inst.get_objs_of_type('OpenLDAPuser')
    real_user_list = ldap_tools.parse_ldap_list(ldap_user_list)

    assert user_list == json.dumps(real_user_list)

    # user_get
    assert json.dumps(
        ErrorCodes.admin['invalidUsername']) == ep.user_get('DoesNotExist')

    user = ep.user_get('slapd')

    ldap_user = inst.get_obj(
        'cusername', 'slapd', objectClass='OpenLDAPuser', throw_error=True)
    assert ldap_user != ()

    ldap_tools.parse_ldap(ldap_user)

    assert json.loads(user) == ldap_user

    # user_virtue_list
    assert json.dumps(ErrorCodes.admin[
        'invalidUsername']) == ep.user_virtue_list('DoesNotExist')

    virtue_list = ep.user_virtue_list('slapd')

    ldap_virtue_list = inst.get_objs_of_type('OpenLDAPvirtue')
    parsed_virtue_list = ldap_tools.parse_ldap_list(ldap_virtue_list)

    real_virtue_list = []

    for v in parsed_virtue_list:
        if (v['username'] == 'slapd'):
            real_virtue_list.append(v)

    assert json.loads(virtue_list) == real_virtue_list

def test_virtue_create():

    subprocess.check_call(['sudo', 'rsync', '/mnt/efs/images/unities/8GB.img',
                           ('/mnt/efs/images/non_provisioned_virtues/'
                            'admintestrole0.img')])

    assert json.dumps(ErrorCodes.admin['invalidUsername']) == ep.virtue_create(
        'DoesNotExist', 'admintestrole0')

    assert json.dumps(ErrorCodes.admin['invalidRoleId']) == ep.virtue_create(
        'slapd', 'DoesNotExist')

    assert json.dumps(
        ErrorCodes.admin['userNotAlreadyAuthorized']) == ep.virtue_create(
            'slapd', 'emptyrole')

    result = json.loads(ep.virtue_create('slapd', 'admintestrole0'))

    assert set(result.keys()) == set(['id', 'ipAddress'])

    global test_virtue_id
    test_virtue_id = result['id']

    time.sleep(1)

    ldap_virtue = inst.get_obj(
        'cid',
        result['id'],
        objectClass='OpenLDAPvirtue',
        throw_error=True)
    ldap_tools.parse_ldap(ldap_virtue)

    assert ldap_virtue['username'] == 'slapd'
    assert ldap_virtue['state'] == 'CREATING'

    # TODO: Make sure loops like these don't continue forever.
    while (ldap_virtue['state'] == 'CREATING'):
        time.sleep(5)
        ldap_virtue = inst.get_obj('cid', result['id'])
        ldap_tools.parse_ldap(ldap_virtue)

    assert ldap_virtue['state'] == 'STOPPED'
    assert os.path.exists(('/mnt/efs/images/provisioned_virtues/'
                           '{0}.img').format(result['id']))

    assert json.dumps(
        ErrorCodes.user['virtueAlreadyExistsForRole']) == ep.virtue_create(
            'slapd', 'admintestrole0')

    inst.del_obj('cid', result['id'], objectClass='OpenLDAPvirtue',
                 throw_error=True)

def test_virtue_destroy():
    
    virtue = {
        'id': 'admintestvirtue0',
        'username': 'NULL',
        'roleId': 'admintestrole0',
        'applicationIds': [],
        'resourceIds': [],
        'transducerIds': [],
        'networkRules': [],
        'state': 'STOPPED',
        'ipAddress': 'NULL'
    }

    ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
    inst.add_obj(ldap_virtue, 'virtues', 'cid', throw_error=True)

    img_path = '/mnt/efs/images/provisioned_virtues/admintestvirtue0.img'

    subprocess.check_call(['sudo', 'rsync', '/mnt/efs/images/unities/8GB.img',
                           img_path])

    assert json.dumps(ErrorCodes.user['invalidId']) == ep.virtue_destroy(
        'DoesNotExist')

    assert ep.virtue_destroy('admintestvirtue0') == json.dumps(
            ErrorCodes.user['success'])

    real_virtue = inst.get_obj(
        'cid',
        'admintestvirtue0',
        objectClass='OpenLDAPvirtue',
        throw_error=True)

    assert real_virtue == ()

    assert not os.path.exists(img_path)
