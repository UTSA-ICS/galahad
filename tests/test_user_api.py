#!/usr/bin/python

import sys
import json
import time

sys.path.insert( 0, '/home/ubuntu/galahad/excalibur' )
from website import ldap_tools
from website.ldaplookup import LDAP
from website.apiendpoint import EndPoint
from website.apiendpoint_admin import EndPoint_Admin
from website.services.errorcodes import ErrorCodes
from website.routes.aws import AWS

def setup_module():

    global inst
    global ep

    inst = LDAP( '', '' )
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s( dn, 'Test123!' )

    ep = EndPoint( 'jmitchell', 'Test123!' )
    ep.inst = inst

    role = {
        'id': 'usertestrole0',
        'name': 'UserTestRole',
        'version': '1.0',
        'applicationIds': ['firefox'],
        'startingResourceIds': [],
        'startingTransducerIds': []
    }

    virtue = {
        'id': 'usertestvirtue0',
        'username': 'NULL',
        'roleId': 'usertestrole0',
        'applicationIds': [],
        'resourceIds': [],
        'transducerIds': [],
        'state': 'STOPPED',
        'ipAddress': '1.2.3.4'
    }

    ldap_role = ldap_tools.to_ldap( role, 'OpenLDAProle' )
    inst.add_obj( ldap_role, 'roles', 'cid', throw_error=True )

    ldap_virtue = ldap_tools.to_ldap( virtue, 'OpenLDAPvirtue' )
    inst.add_obj( ldap_virtue, 'virtues', 'cid', throw_error=True )

    user = inst.get_obj( 'cusername', 'jmitchell', objectClass='OpenLDAPuser', throw_error=True )
    ldap_tools.parse_ldap( user )

    if( 'usertestrole0' not in user['authorizedRoleIds'] ):
        user['authorizedRoleIds'].append( 'usertestrole0' )
        ldap_user = ldap_tools.to_ldap( user, 'OpenLDAPuser' )
        inst.modify_obj( 'cusername', 'jmitchell', ldap_user, objectClass='OpenLDAPuser', throw_error=True )

def teardown_module():

    user = inst.get_obj( 'cusername', 'jmitchell', objectClass='OpenLDAPuser', throw_error=True )
    ldap_tools.parse_ldap( user )

    user['authorizedRoleIds'].remove( 'usertestrole0' )
    ldap_user = ldap_tools.to_ldap( user, 'OpenLDAPuser' )
    inst.modify_obj( 'cusername', 'jmitchell', ldap_user, objectClass='OpenLDAPuser', throw_error=True )

    inst.del_obj( 'cid', 'usertestrole0', objectClass='OpenLDAProle', throw_error=True )

def test_application_calls():
    # application_get
    assert json.dumps( ErrorCodes.user['invalidId'] ) == ep.application_get( 'jmitchell', 'DoesNotExist' )

    assert json.dumps( ErrorCodes.user['userNotAuthorized'] ) == ep.application_get( 'jmitchell', 'xterm' )

    app = json.loads( ep.application_get( 'jmitchell', 'firefox' ) )

    real_app = inst.get_obj( 'cid', 'firefox', objectClass='OpenLDAPapplication', throw_error=True )
    ldap_tools.parse_ldap( real_app )

    assert app == real_app

def test_role_calls():
    # role_get
    assert json.dumps( ErrorCodes.user['invalidId'] ) == ep.role_get( 'jmitchell', 'DoesNotExist' )

    assert json.dumps( ErrorCodes.user['userNotAuthorized'] ) == ep.role_get( 'jmitchell', 'emptyrole' )

    role = json.loads( ep.role_get( 'jmitchell', 'usertestrole0' ) )

    real_role = inst.get_obj( 'cid', 'usertestrole0', objectClass='OpenLDAProle', throw_error=True )
    ldap_tools.parse_ldap( real_role )

    # role_get also returns an ip address for that user/role's virtue.
    # The user shouldn't have one, because virtue_create hasn't been tested/called.
    real_role['ipAddress'] = 'NULL'

    assert role == real_role


    # user_role_list
    user = inst.get_obj( 'cusername', 'jmitchell', 'OpenLDAPuser', True )
    ldap_tools.parse_ldap( user )

    roles = json.loads( ep.user_role_list( 'jmitchell' ) )

    real_roles = []

    for r in user['authorizedRoleIds']:
        role = inst.get_obj( 'cid', r, 'OpenLDAProle', True )
        ldap_tools.parse_ldap( role )

        if( role != () ):
            ldap_tools.parse_ldap( role )
            role['ipAddress'] = 'NULL'
            real_roles.append( role )

    if( roles != real_roles ):
        print( roles )
        print
        print( real_roles )

    assert roles == real_roles

    assert ep.user_role_list( 'fpatwa' ) == json.dumps( [] )

def test_virtue_calls():
    # virtue_create
    assert json.dumps( ErrorCodes.user['invalidRoleId'] ) == ep.virtue_create( 'jmitchell', 'DoesNotExist', use_aws=False )

    assert json.dumps( ErrorCodes.user['userNotAuthorizedForRole'] ) == ep.virtue_create( 'jmitchell', 'emptyrole', use_aws=False )

    result = json.loads( ep.virtue_create( 'jmitchell', 'usertestrole0', use_aws=False ) )

    real_virtue = inst.get_obj( 'cid', 'usertestvirtue0', objectClass='OpenLDAPvirtue', throw_error=True )
    ldap_tools.parse_ldap( real_virtue )

    assert result['id'] == 'usertestvirtue0'
    assert result['ipAddress'] == real_virtue['ipAddress']

    assert real_virtue['username'] == 'jmitchell'

    assert json.dumps( ErrorCodes.user['virtueAlreadyExistsForRole'] ) == ep.virtue_create( 'jmitchell', 'usertestrole0', use_aws=False )


    # virtue_get
    assert json.dumps( ErrorCodes.user['invalidId'] ) == ep.virtue_get( 'jmitchell', 'DoesNotExist' )

    assert json.dumps( ErrorCodes.user['userNotAuthorized'] ) == ep.virtue_get( 'fpatwa', 'usertestvirtue0' )

    virtue = json.loads( ep.virtue_get( 'jmitchell', 'usertestvirtue0' ) )

    assert virtue == real_virtue


    # user_virtue_list
    virtues = json.loads( ep.user_virtue_list( 'jmitchell' ) )

    assert virtues == [real_virtue]

    assert ep.user_virtue_list( 'fpatwa' ) == json.dumps( [] )


    # virtue_launch (NotImplemented)
    # virtue_stop (NotImplemented)
    # virtue_destroy
    assert json.dumps( ErrorCodes.user['invalidId'] ) == ep.virtue_destroy( 'jmitchell', 'DoesNotExist', use_aws=False )

    assert json.dumps( ErrorCodes.user['userNotAuthorized'] ) == ep.virtue_destroy( 'fpatwa', 'usertestvirtue0', use_aws=False )

    ldap_virtue = inst.get_obj( 'cid', 'usertestvirtue0', objectClass='OpenLDAPvirtue', throw_error=True )
    ldap_virtue['cstate'] = 'RUNNING'
    inst.modify_obj( 'cid', 'usertestvirtue0', ldap_virtue, objectClass='OpenLDAPvirtue' )

    assert json.dumps( ErrorCodes.user['virtueNotStopped'] ) == ep.virtue_destroy( 'jmitchell', 'usertestvirtue0' )

    ldap_virtue['cstate'] = 'STOPPED'
    inst.modify_obj( 'cid', 'usertestvirtue0', ldap_virtue, objectClass='OpenLDAPvirtue' )

    assert ep.virtue_destroy( 'jmitchell', 'usertestvirtue0', use_aws=False ) == None

    virtue = json.loads( ep.virtue_get( 'jmitchell', 'usertestvirtue0' ) )

    assert ( virtue == ErrorCodes.user['invalidId'] or virtue['state'] == 'DELETING' )


    # virtue_application_launch (NotImplemented)
    # virtue_application_stop (NotImplemented)
