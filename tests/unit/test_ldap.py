#!/usr/bin/python

# Copyright (c) 2019 by Star Lab Corp.

import copy
import os
import sys
import json
import traceback

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(file_path)) + '/../excalibur'
sys.path.insert(0, base_excalibur_dir)
from website.ldaplookup import LDAP
from website import ldap_tools


def setup_module():

    global inst
    global ad_inst
    global ep

    inst = LDAP('', '')
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s(dn, 'Test123!')

    ad_inst = LDAP('slapd@virtue.gov', 'Test123!')
    ad_inst.bind_ad()


def test_get_obj():

    user = inst.get_obj(
        'cusername', 'slapd', objectClass='OpenLDAPuser', throw_error=True)

    slapd_name = ad_inst.query_ad('cn', 'slapd')[0][1]['sAMAccountName'][0]

    assert user == {
        'cusername': ['slapd'],
        'cauthRoleIds': ['[]'],
        'ou': ['virtue'],
        'objectClass': ['OpenLDAPuser'],
        'name': [json.dumps(slapd_name)]
    }

    ldap_tools.parse_ldap(user)

    assert user == {
        'username': 'slapd',
        'authorizedRoleIds': [],
        'name': slapd_name
    }


def test_objs_of_type():

    users = inst.get_objs_of_type('OpenLDAPuser')

    slapd_name = ad_inst.query_ad('cn', 'slapd')[0][1]['sAMAccountName'][0]
    assert (
        'cusername=slapd,cn=users,ou=virtue,dc=canvas,dc=virtue,dc=com', {
            'cusername': ['slapd'],
            'cauthRoleIds': ['[]'],
            'ou': ['virtue'],
            'objectClass': ['OpenLDAPuser'],
            'name': [json.dumps(slapd_name)]
        }) in users

    fpatwa_name = ad_inst.query_ad('cn', 'fpatwa')[0][1]['sAMAccountName'][0]
    assert (
        'cusername=fpatwa,cn=users,ou=virtue,dc=canvas,dc=virtue,dc=com', {
            'cusername': ['fpatwa'],
            'cauthRoleIds': ['[]'],
            'ou': ['virtue'],
            'objectClass': ['OpenLDAPuser'],
            'name': [json.dumps(fpatwa_name)]
        }) in users

    jbenson_name = ad_inst.query_ad('cn', 'jbenson')[0][1]['sAMAccountName'][0]
    assert (
        'cusername=jbenson,cn=users,ou=virtue,dc=canvas,dc=virtue,dc=com', {
            'cusername': ['jbenson'],
            'cauthRoleIds': ['[]'],
            'ou': ['virtue'],
            'objectClass': ['OpenLDAPuser'],
            'name': [json.dumps(jbenson_name)]
        }) in users

    users_parsed = ldap_tools.parse_ldap_list(users)

    assert {
        'username': 'slapd',
        'authorizedRoleIds': [],
        'name': slapd_name
    } in users_parsed

    assert {
        'username': 'fpatwa',
        'authorizedRoleIds': [],
        'name': fpatwa_name
    } in users_parsed

    assert {
        'username': 'jbenson',
        'authorizedRoleIds': [],
        'name': jbenson_name
    } in users_parsed


def test_write_to_ldap():

    temp_role = {
        'id': 'routeradmin',
        'name': 'Router Admin',
        'applicationIds': ['firefox', 'xterm'],
        'startingResourceIds': [],
        'startingTransducerIds': [],
        'networkRules': [],
        'version': '1.0'
    }

    ldap_temp_role = ldap_tools.to_ldap(temp_role, 'OpenLDAProle')

    assert ldap_temp_role == {
        'objectClass': 'OpenLDAProle',
        'ou': 'virtue',
        'cid': 'routeradmin',
        'name': '"Router Admin"',
        'cversion': '"1.0"',
        'cappIds': json.dumps(['firefox', 'xterm']),
        'cstartResIds': '[]',
        'cstartTransIds': '[]',
        'cnetRules': '[]'
    }

    try:

        assert 0 == inst.add_obj(
            ldap_temp_role, 'roles', 'cid', throw_error=True)

        ldap_temp_role_2 = inst.get_obj(
            'cid', 'routeradmin', objectClass='OpenLDAProle', throw_error=True)

        temp_role_2 = copy.deepcopy(ldap_temp_role_2)
        ldap_tools.parse_ldap(temp_role_2)

        assert temp_role == temp_role_2

        ldap_temp_role_2['cversion'] = ['1.1']

        assert 0 == inst.modify_obj(
            'cid',
            'routeradmin',
            ldap_temp_role_2,
            objectClass='OpenLDAProle',
            throw_error=True)

        ldap_temp_role_3 = inst.get_obj(
            'cid', 'routeradmin', objectClass='OpenLDAProle', throw_error=True)

        assert ldap_temp_role_2 == ldap_temp_role_3

        assert 0 == inst.del_obj(
            'cid', 'routeradmin', objectClass='OpenLDAProle', throw_error=True)

    except Exception as e:
        inst.del_obj('cid', 'routeradmin', objectClass='OpenLDAProle')
        traceback.print_exc()
        pass

    assert () == inst.get_obj(
        'cid', 'routeradmin', objectClass='OpenLDAProle', throw_error=True)
