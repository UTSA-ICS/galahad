#!/usr/bin/python

import os
import sys
import json
import time

sys.path.insert( 0, '/home/ubuntu/galahad/flask-authlib' )
from website import ldap_tools
from website.ldaplookup import LDAP
from website.apiendpoint import EndPoint
from website.apiendpoint_admin import EndPoint_Admin
from website.services.errorcodes import ErrorCodes
from website.routes.aws import AWS

if( __name__ == '__main__' ):

    inst = LDAP( '', '' )
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s( dn, 'Test123!' )

    ep = EndPoint( 'jmitchell', 'Test123!' )
    ep.inst = inst

    epa = EndPoint_Admin( 'jmitchell', 'Test123!' )
    epa.inst = inst

    # Assume the admin test has been run first,
    # and the browsing role has been created

    # Test...
    # application_get
    assert json.dumps( ErrorCodes.user['invalidId'] ) == ep.application_get( 'jmitchell', 'DoesNotExist' )

    role = inst.get_obj( 'name', 'browsing', objectClass='OpenLDAProle', throw_error=True )
    assert role != ()
    ldap_tools.parse_ldap( role )

    user = inst.get_obj( 'cusername', 'jmitchell', objectClass='OpenLDAPuser', throw_error=True )
    ldap_tools.parse_ldap( user )

    test_role_id = role['id']

    # Authorize the user if they aren't already
    if( test_role_id not in user['authorizedRoleIds'] ):
        epa.user_role_authorize( 'jmitchell', test_role_id )

    assert json.dumps( ErrorCodes.user['userNotAuthorized'] ) == ep.application_get( 'jmitchell', 'xterm' )

    app = json.loads( ep.application_get( 'jmitchell', 'firefox' ) )

    real_app = inst.get_obj( 'cid', 'firefox', objectClass='OpenLDAPapplication', throw_error=True )
    ldap_tools.parse_ldap( real_app )

    assert app == real_app


    # role_get
    assert json.dumps( ErrorCodes.user['invalidId'] ) == ep.role_get( 'jmitchell', 'DoesNotExist' )

    assert json.dumps( ErrorCodes.user['userNotAuthorized'] ) == ep.role_get( 'jmitchell', 'emptyrole' )

    role = json.loads( ep.role_get( 'jmitchell', test_role_id ) )

    real_role = inst.get_obj( 'cid', test_role_id, objectClass='OpenLDAProle', throw_error=True )
    ldap_tools.parse_ldap( real_role )

    # role_get also returns an ip address for that user/role's virtue.
    # The user shouldn't have one, because virtue_create hasn't been tested/called.
    real_role['ipAddress'] = 'NULL'

    assert role == real_role


    # user_role_list
    user = inst.get_obj( 'cusername', 'jmitchell', 'OpenLDAPuser', True )
    ldap_tools.parse_ldap( user )

    roles = json.loads( ep.user_role_list( 'jmitchell' ) )

    ldap_real_roles = inst.get_objs_of_type( 'OpenLDAProle' )
    real_roles = ldap_tools.parse_ldap_list( ldap_real_roles )

    real_roles = []

    for r in user['authorizedRoleIds']:
        role = inst.get_obj( 'cid', r, 'OpenLDAProle', True )
        ldap_tools.parse_ldap( role )

        if( role != () ):
            ldap_tools.parse_ldap( role )
            role['ipAddress'] = 'NULL'
            real_roles.append( role )

    '''for r in real_roles:
        # user_role_list also returns an ip address for that user/role's virtue.
        r['ipAddress'] = 'NULL'''

    if( roles != real_roles ):
        print( roles )
        print
        print( real_roles )

    assert roles == real_roles

    assert ep.user_role_list( 'fpatwa' ) == json.dumps( [] )

    
    # virtue_create
    assert json.dumps( ErrorCodes.user['invalidRoleId'] ) == ep.virtue_create( 'jmitchell', 'DoesNotExist' )

    assert json.dumps( ErrorCodes.user['userNotAuthorizedForRole'] ) == ep.virtue_create( 'jmitchell', 'emptyrole' )

    result = json.loads( ep.virtue_create( 'jmitchell', test_role_id ) )

    real_virtue = inst.get_obj( 'cid', result['id'], objectClass='OpenLDAPvirtue', throw_error=True )
    ldap_tools.parse_ldap( real_virtue )

    assert result['id'] == real_virtue['id']
    assert result['ipAddress'] == real_virtue['ipAddress']

    assert AWS.get_id_from_ip( real_virtue['ipAddress'] ) != None

    test_virtue_id = real_virtue['id']

    assert json.dumps( ErrorCodes.user['virtueAlreadyExistsForRole'] ) == ep.virtue_create( 'jmitchell', test_role_id )

    # virtue_get
    assert json.dumps( ErrorCodes.user['invalidId'] ) == ep.virtue_get( 'jmitchell', 'DoesNotExist' )

    assert json.dumps( ErrorCodes.user['userNotAuthorized'] ) == ep.virtue_get( 'fpatwa', test_virtue_id )

    virtue = json.loads( ep.virtue_get( 'jmitchell', test_virtue_id ) )

    assert virtue == real_virtue


    # user_virtue_list
    virtues = json.loads( ep.user_virtue_list( 'jmitchell' ) )

    assert virtues == [real_virtue]

    assert ep.user_virtue_list( 'fpatwa' ) == json.dumps( [] )


    # virtue_launch (NotImplemented)
    # virtue_stop (NotImplemented)
    # virtue_destroy
    assert json.dumps( ErrorCodes.user['invalidId'] ) == ep.virtue_destroy( 'jmitchell', 'DoesNotExist' )

    assert json.dumps( ErrorCodes.user['userNotAuthorized'] ) == ep.virtue_destroy( 'fpatwa', test_virtue_id )

    ldap_virtue = inst.get_obj( 'cid', test_virtue_id, objectClass='OpenLDAPvirtue', throw_error=True )
    ldap_virtue['cstate'] = 'STOPPED'
    inst.modify_obj( 'cid', test_virtue_id, ldap_virtue, objectClass='OpenLDAPvirtue' )

    assert ep.virtue_destroy( 'jmitchell', test_virtue_id ) == None

    virtue = json.loads( ep.virtue_get( 'jmitchell', test_virtue_id ) )

    assert ( virtue == ErrorCodes.user['invalidId'] or virtue['state'] == 'DELETING' )


    # virtue_application_launch (NotImplemented)
    # virtue_application_stop (NotImplemented)
