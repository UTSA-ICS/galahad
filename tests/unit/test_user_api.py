#!/usr/bin/python

import json
import os
import sys
import time

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(file_path)) + '/../excalibur'
sys.path.insert(0, base_excalibur_dir)
from website import ldap_tools
from website.ldaplookup import LDAP
from website.apiendpoint import EndPoint
from website.apiendpoint_admin import EndPoint_Admin
from website.services.errorcodes import ErrorCodes
from website.aws import AWS


def setup_module():

    global inst
    global ep

    inst = LDAP('', '')
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s(dn, 'Test123!')

    ep = EndPoint('jmitchell', 'Test123!')
    ep.inst = inst

    role = {
        'id': 'usertestrole0',
        'name': 'UserTestRole',
        'version': '1.0',
        'applicationIds': ['firefox'],
        'startingResourceIds': [],
        'startingTransducerIds': [],
    }

    virtue = {
        'id': 'usertestvirtue0',
        'username': 'jmitchell',
        'roleId': 'usertestrole0',
        'applicationIds': [],
        'resourceIds': [],
        'transducerIds': [],
        'state': 'STOPPED',
        'ipAddress': 'NULL'
    }

    ldap_role = ldap_tools.to_ldap(role, 'OpenLDAProle')
    inst.add_obj(ldap_role, 'roles', 'cid', throw_error=True)

    ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
    inst.add_obj(ldap_virtue, 'virtues', 'cid', throw_error=True)

    user = inst.get_obj(
        'cusername', 'jmitchell', objectClass='OpenLDAPuser', throw_error=True)
    ldap_tools.parse_ldap(user)

    if ('usertestrole0' not in user['authorizedRoleIds']):
        user['authorizedRoleIds'].append('usertestrole0')
        ldap_user = ldap_tools.to_ldap(user, 'OpenLDAPuser')
        inst.modify_obj(
            'cusername',
            'jmitchell',
            ldap_user,
            objectClass='OpenLDAPuser',
            throw_error=True)


def teardown_module():

    user = inst.get_obj(
        'cusername', 'jmitchell', objectClass='OpenLDAPuser', throw_error=True)
    ldap_tools.parse_ldap(user)

    user['authorizedRoleIds'].remove('usertestrole0')
    ldap_user = ldap_tools.to_ldap(user, 'OpenLDAPuser')
    inst.modify_obj(
        'cusername',
        'jmitchell',
        ldap_user,
        objectClass='OpenLDAPuser',
        throw_error=True)

    inst.del_obj(
        'cid', 'usertestrole0', objectClass='OpenLDAProle', throw_error=True)

    inst.del_obj(
        'cid', 'usertestvirtue0', objectClass='OpenLDAPvirtue', throw_error=True)


def test_application_calls():
    # application_get
    assert json.dumps(ErrorCodes.user['invalidId']) == ep.application_get(
        'jmitchell', 'DoesNotExist')

    assert json.dumps(
        ErrorCodes.user['userNotAuthorized']) == ep.application_get(
            'jmitchell', 'xterm')

    app = json.loads(ep.application_get('jmitchell', 'firefox'))

    real_app = inst.get_obj(
        'cid', 'firefox', objectClass='OpenLDAPapplication', throw_error=True)
    ldap_tools.parse_ldap(real_app)

    assert app == real_app


def test_role_calls():
    # role_get
    assert json.dumps(ErrorCodes.user['invalidId']) == ep.role_get(
        'jmitchell', 'DoesNotExist')

    assert json.dumps(ErrorCodes.user['userNotAuthorized']) == ep.role_get(
        'jmitchell', 'emptyrole')

    role = json.loads(ep.role_get('jmitchell', 'usertestrole0'))

    real_role = inst.get_obj(
        'cid', 'usertestrole0', objectClass='OpenLDAProle', throw_error=True)
    ldap_tools.parse_ldap(real_role)

    # role_get also returns an ip address for that user/role's virtue.
    # The user shouldn't have one, because virtue_create hasn't been tested/called.
    real_role['ipAddress'] = 'NULL'

    assert role == real_role

    # user_role_list
    user = inst.get_obj('cusername', 'jmitchell', 'OpenLDAPuser', True)
    ldap_tools.parse_ldap(user)

    roles = json.loads(ep.user_role_list('jmitchell'))

    real_roles = []

    for r in user['authorizedRoleIds']:
        role = inst.get_obj('cid', r, 'OpenLDAProle', True)

        if (role != ()):
            ldap_tools.parse_ldap(role)
            role['ipAddress'] = 'NULL'
            real_roles.append(role)

    if (roles != real_roles):
        print(roles)
        print
        print(real_roles)

    assert roles == real_roles

    assert ep.user_role_list('fpatwa') == json.dumps([])


def test_virtue_calls():

    # virtue_get
    assert json.dumps(ErrorCodes.user['invalidId']) == ep.virtue_get(
        'jmitchell', 'DoesNotExist')

    assert json.dumps(ErrorCodes.user['userNotAuthorized']) == ep.virtue_get(
        'fpatwa', 'usertestvirtue0')

    virtue = json.loads(ep.virtue_get('jmitchell', 'usertestvirtue0'))

    real_virtue = inst.get_obj(
        'cid',
        'usertestvirtue0',
        objectClass='OpenLDAPvirtue',
        throw_error=True)
    ldap_tools.parse_ldap(real_virtue)

    real_virtue = {
        'id': real_virtue['id'],
        'username': real_virtue['username'],
        'roleId': real_virtue['roleId'],
        'applicationIds': real_virtue['applicationIds'],
        'resourceIds': real_virtue['resourceIds'],
        'transducerIds': real_virtue['transducerIds'],
        'state': real_virtue['state'],
        'ipAddress': real_virtue['ipAddress']
    }
    assert virtue == real_virtue

    # user_virtue_list
    virtues = json.loads(ep.user_virtue_list('jmitchell'))

    assert virtues == [real_virtue]

    assert ep.user_virtue_list('fpatwa') == json.dumps([])

    # virtue_launch
    assert (json.dumps(ErrorCodes.user['invalidId']) ==
            ep.virtue_launch('jmitchell', 'DoesNotExist', use_valor=False))

    assert (json.dumps(ErrorCodes.user['userNotAuthorized']) ==
            ep.virtue_launch('fpatwa', 'usertestvirtue0', use_valor=False))

    assert (json.dumps(ErrorCodes.user['success']) ==
            ep.virtue_launch('jmitchell', 'usertestvirtue0', use_valor=False))

    real_virtue = inst.get_obj(
        'cid',
        'usertestvirtue0',
        objectClass='OpenLDAPvirtue',
        throw_error=True)
    ldap_tools.parse_ldap(real_virtue)
    assert real_virtue['state'] == 'RUNNING'

    # virtue_application_launch
    assert (json.dumps(ErrorCodes.user['userNotAuthorized']) ==
            ep.virtue_application_launch('fpatwa', 'usertestvirtue0',
                                         'firefox', use_ssh=False))

    assert (json.dumps(ErrorCodes.user['invalidVirtueId']) ==
            ep.virtue_application_launch('jmitchell', 'DoesNotExist',
                                         'firefox', use_ssh=False))

    assert (json.dumps(ErrorCodes.user['invalidApplicationId']) ==
            ep.virtue_application_launch('jmitchell', 'usertestvirtue0',
                                         'DoesNotExist', use_ssh=False))

    assert (json.dumps(ErrorCodes.user['applicationNotInVirtue']) ==
            ep.virtue_application_launch('jmitchell', 'usertestvirtue0',
                                         'xterm', use_ssh=False))

    assert (json.dumps(ErrorCodes.user['success']) ==
            ep.virtue_application_launch('jmitchell', 'usertestvirtue0',
                                         'firefox', use_ssh=False))
    real_virtue = inst.get_obj(
        'cid',
        'usertestvirtue0',
        objectClass='OpenLDAPvirtue',
        throw_error=True)
    ldap_tools.parse_ldap(real_virtue)
    assert real_virtue['applicationIds'] == ['firefox']

    assert (json.dumps(ErrorCodes.user['applicationAlreadyLaunched']) ==
            ep.virtue_application_launch('jmitchell', 'usertestvirtue0',
                                         'firefox', use_ssh=False))

    # virtue_application_stop
    assert (json.dumps(ErrorCodes.user['userNotAuthorized']) ==
            ep.virtue_application_stop('fpatwa', 'usertestvirtue0',
                                       'firefox', use_ssh=False))

    assert (json.dumps(ErrorCodes.user['invalidVirtueId']) ==
            ep.virtue_application_stop('jmitchell', 'DoesNotExist',
                                       'firefox', use_ssh=False))

    assert (json.dumps(ErrorCodes.user['invalidApplicationId']) ==
            ep.virtue_application_stop('jmitchell', 'usertestvirtue0',
                                       'DoesNotExist', use_ssh=False))

    assert (json.dumps(ErrorCodes.user['applicationNotInVirtue']) ==
            ep.virtue_application_stop('jmitchell', 'usertestvirtue0',
                                       'xterm', use_ssh=False))

    assert (json.dumps(ErrorCodes.user['success']) ==
            ep.virtue_application_stop('jmitchell', 'usertestvirtue0',
                                       'firefox', use_ssh=False))
    real_virtue = inst.get_obj(
        'cid',
        'usertestvirtue0',
        objectClass='OpenLDAPvirtue',
        throw_error=True)
    ldap_tools.parse_ldap(real_virtue)
    assert real_virtue['applicationIds'] == []

    assert (json.dumps(ErrorCodes.user['applicationAlreadyStopped']) ==
            ep.virtue_application_stop('jmitchell', 'usertestvirtue0',
                                       'firefox', use_ssh=False))


    # virtue_stop
    assert (json.dumps(ErrorCodes.user['invalidId']) ==
            ep.virtue_stop('jmitchell', 'DoesNotExist', use_valor=False))

    assert (json.dumps(ErrorCodes.user['userNotAuthorized']) ==
            ep.virtue_stop('fpatwa', 'usertestvirtue0', use_valor=False))

    assert (json.dumps(ErrorCodes.user['success']) ==
            ep.virtue_stop('jmitchell', 'usertestvirtue0', use_valor=False))


def test_key_calls():

    # key_get
    key = json.loads(ep.key_get('jmitchell'))
    assert '-----BEGIN RSA PRIVATE KEY-----' in key
    assert '-----END RSA PRIVATE KEY-----' in key
