#!/usr/bin/python

import json
import os
import sys

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

    inst = LDAP('', '')
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s(dn, 'Test123!')

    ep = EndPoint_Admin('jmitchell', 'Test123!')
    ep.inst = inst

    role = {
        'id': 'admintestrole0',
        'name': 'AdminTestRole',
        'version': '1.0',
        'applicationIds': ['firefox'],
        'startingResourceIds': [],
        'startingTransducerIds': [],
        'amiId': 'NULL'
    }

    virtue = {
        'id': 'admintestvirtue0',
        'username': 'NULL',
        'roleId': 'admintestrole0',
        'applicationIds': [],
        'resourceIds': [],
        'transducerIds': [],
        'awsInstanceId': 'NULL'
    }

    ldap_role = ldap_tools.to_ldap(role, 'OpenLDAProle')
    inst.add_obj(ldap_role, 'roles', 'cid', throw_error=True)

    ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
    inst.add_obj(ldap_virtue, 'virtues', 'cid', throw_error=True)

    user = inst.get_obj(
        'cusername', 'jmitchell', objectClass='OpenLDAPuser', throw_error=True)
    ldap_tools.parse_ldap(user)

    if ('admintestrole0' not in user['authorizedRoleIds']):
        user['authorizedRoleIds'].append('admintestrole0')
        ldap_user = ldap_tools.to_ldap(user, 'OpenLDAPuser')
        inst.modify_obj(
            'cusername',
            'jmitchell',
            ldap_user,
            objectClass='OpenLDAPuser',
            throw_error=True)

    # set to satisfy pytest when listing tests
    test_role_id = None

def teardown_module():

    inst.del_obj(
        'cid', 'admintestrole0', objectClass='OpenLDAProle', throw_error=True)

    inst.del_obj(
        'cid', 'admintestvirtue0', objectClass='OpenLDAPvirtue', throw_error=True)

    if test_role_id is not None:
        inst.del_obj(
            'cid', test_role_id, objectClass='OpenLDAProle', throw_error=True)

    user = inst.get_obj(
        'cusername', 'jmitchell', objectClass='OpenLDAPuser', throw_error=True)
    ldap_tools.parse_ldap(user)

    user['authorizedRoleIds'].remove('admintestrole0')
    ldap_user = ldap_tools.to_ldap(user, 'OpenLDAPuser')
    inst.modify_obj(
        'cusername',
        'jmitchell',
        ldap_user,
        objectClass='OpenLDAPuser',
        throw_error=True)

    if test_role_id is not None:
        virtue = inst.get_obj(
            'croleId',
            test_role_id,
            objectClass='OpenLDAPvirtue',
            throw_error=True)

        assert inst.del_obj(
            'cid',
            virtue['cid'][0],
            objectClass='OpenLDAPvirtue',
            throw_error=True) == 0


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
        'startingTransducerIds': []
    }

    bad_role_1 = {
        'version': '1.0',
        'applicationIds': ['firefox', 'thunderbird'],
        'startingResourceIds': ['fileshare1'],
        'startingTransducerIds': []
    }

    bad_role_2 = {
        'id': 'NotRelevant',
        'name': 'browsing',
        'version': '1.0',
        'applicationIds': "['firefox', 'thunderbird']",
        'startingResourceIds': "['fileshare1']",
        'startingTransducerIds': "[]"
    }

    bad_role_3 = {
        'id': 'NotRelevant',
        'name': 'browsing',
        'version': '1.0',
        'applicationIds': ['firefox', 'thunderbird', 'DoesNotExist'],
        'startingResourceIds': ['fileshare1'],
        'startingTransducerIds': []
    }

    bad_role_4 = {
        'id': 'NotRelevant',
        'name': 'browsing',
        'version': '1.0',
        'applicationIds': ['firefox', 'thunderbird'],
        'startingResourceIds': ['fileshare1', 'DoesNotExist'],
        'startingTransducerIds': []
    }

    bad_role_5 = {
        'id': 'NotRelevant',
        'name': 'browsing',
        'version': '1.0',
        'applicationIds': ['firefox', 'thunderbird'],
        'startingResourceIds': ['fileshare1'],
        'startingTransducerIds': ['DoesNotExist']
    }

    assert json.dumps(ErrorCodes.admin['invalidFormat']) == ep.role_create(
        bad_role_1, use_aws=False)
    assert json.dumps(ErrorCodes.admin['invalidFormat']) == ep.role_create(
        bad_role_2, use_aws=False)

    assert json.dumps(
        ErrorCodes.admin['invalidApplicationId']) == ep.role_create(
            bad_role_3, use_aws=False)

    assert json.dumps(ErrorCodes.admin['invalidResourceId']) == ep.role_create(
        bad_role_4, use_aws=False)

    assert json.dumps(
        ErrorCodes.admin['invalidTransducerId']) == ep.role_create(
            bad_role_5, use_aws=False)

    result_role_json = ep.role_create(good_role, use_aws=False)

    result_role = json.loads(result_role_json)

    # role create should ignore the ID provided
    assert result_role['id'] != 'NotRelevant'
    assert result_role == {'id': result_role['id'], 'name': good_role['name']}

    good_role['id'] = result_role['id']

    ldap_role = inst.get_obj('cid', result_role['id'])
    ldap_tools.parse_ldap( ldap_role )
    del ldap_role['amiId']
    assert ldap_role == good_role

    # This will be used in teardown_module()
    global test_role_id
    test_role_id = result_role['id']

    # role_list
    role_list = ep.role_list()

    ldap_role_list = inst.get_objs_of_type('OpenLDAProle')
    real_role_list = ldap_tools.parse_ldap_list(ldap_role_list)

    for role in real_role_list:
        del role['amiId']

    assert role_list == json.dumps(real_role_list)

    # user_role_authorize
    assert json.dumps(
        ErrorCodes.admin['invalidUsername']) == ep.user_role_authorize(
            'DoesNotExist', test_role_id)

    assert json.dumps(
        ErrorCodes.admin['invalidRoleId']) == ep.user_role_authorize(
            'jmitchell', 'DoesNotExist')

    # user_role_authorize only returns when there's an error
    assert ep.user_role_authorize('jmitchell', test_role_id) == json.dumps(
        ErrorCodes.admin['success'])

    # Make sure LDAP has been updated
    user = inst.get_obj(
        'cusername', 'jmitchell', objectClass='OpenLDAPuser', throw_error=True)
    ldap_tools.parse_ldap(user)

    assert test_role_id in user['authorizedRoleIds']

    # Try to authorize twice
    assert json.dumps(
        ErrorCodes.admin['userAlreadyAuthorized']) == ep.user_role_authorize(
            'jmitchell', test_role_id)

    # user_role_unauthorize
    assert json.dumps(
        ErrorCodes.admin['invalidUsername']) == ep.user_role_unauthorize(
            'DoesNotExist', test_role_id)

    assert json.dumps(
        ErrorCodes.admin['invalidRoleId']) == ep.user_role_unauthorize(
            'jmitchell', 'DoesNotExist')

    # Todo: Check return when user is using a virtue

    # user_role_unauthorize only returns when there's an error
    assert ep.user_role_unauthorize('jmitchell', test_role_id) == json.dumps(
        ErrorCodes.admin['success'])

    # Make sure LDAP has been updated
    user = inst.get_obj(
        'cusername', 'jmitchell', objectClass='OpenLDAPuser', throw_error=True)
    ldap_tools.parse_ldap(user)

    assert test_role_id not in user['authorizedRoleIds']

    # Try to unauthorize twice
    assert json.dumps(ErrorCodes.admin[
        'userNotAlreadyAuthorized']) == ep.user_role_unauthorize(
            'jmitchell', test_role_id)

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

    user = ep.user_get('jmitchell')

    ldap_user = inst.get_obj(
        'cusername', 'jmitchell', objectClass='OpenLDAPuser', throw_error=True)
    assert ldap_user != ()

    ldap_tools.parse_ldap(ldap_user)

    assert json.loads(user) == ldap_user

    # user_virtue_list
    assert json.dumps(ErrorCodes.admin[
        'invalidUsername']) == ep.user_virtue_list('DoesNotExist')

    virtue_list = ep.user_virtue_list('jmitchell')

    ldap_virtue_list = inst.get_objs_of_type('OpenLDAPvirtue')
    parsed_virtue_list = ldap_tools.parse_ldap_list(ldap_virtue_list)

    real_virtue_list = []

    for v in parsed_virtue_list:
        if (v['username'] == 'jmitchell'):
            del v['awsInstanceId']
            v['state'] = 'NULL'
            v['ipAddress'] = 'NULL'
            real_virtue_list.append(v)

    assert json.loads(virtue_list) == real_virtue_list

def test_virtue_create():

    assert json.dumps(ErrorCodes.admin['invalidUsername']) == ep.virtue_create(
        'DoesNotExist', 'admintestrole0', use_aws=False)

    assert json.dumps(ErrorCodes.admin['invalidRoleId']) == ep.virtue_create(
        'jmitchell', 'DoesNotExist', use_aws=False)

    assert json.dumps(
        ErrorCodes.admin['userNotAlreadyAuthorized']) == ep.virtue_create(
            'jmitchell', 'emptyrole', use_aws=False)

    result = json.loads(
        ep.virtue_create('jmitchell', 'admintestrole0', use_aws=False))

    real_virtue = inst.get_obj(
        'cid',
        'admintestvirtue0',
        objectClass='OpenLDAPvirtue',
        throw_error=True)
    ldap_tools.parse_ldap(real_virtue)

    assert result == {
        'id': 'admintestvirtue0',
        'ipAddress': 'NULL'
    }

    assert real_virtue['username'] == 'jmitchell'

    assert json.dumps(
        ErrorCodes.user['virtueAlreadyExistsForRole']) == ep.virtue_create(
            'jmitchell', 'admintestrole0', use_aws=False)

def test_virtue_destroy():

    assert json.dumps(ErrorCodes.user['invalidId']) == ep.virtue_destroy(
        'DoesNotExist', use_aws=False)

    assert ep.virtue_destroy(
        'admintestvirtue0', use_aws=False) == json.dumps(
            ErrorCodes.user['success'])

    real_virtue = inst.get_obj(
        'cid',
        'admintestvirtue0',
        objectClass='OpenLDAPvirtue',
        throw_error=True)

    assert real_virtue == ()
