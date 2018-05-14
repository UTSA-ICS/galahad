#!/usr/bin/python

import sys
import ldap
import ldap.modlist

sys.path.insert( 0, '/home/ubuntu/galahad/flask-authlib' )
from website.ldaplookup import LDAP
from website.ldap_tools import to_ldap

LDAP_VIRTUE_DN = "ou=virtue,dc=canvas,dc=virtue,dc=com"

def add_subtree( name, gid ):

    tree = ldap.modlist.addModlist( {
        'objectClass': ['top', 'posixGroup'],
        'gidNumber': str(gid),
        'cn': name
    } )

    inst.conn.add_s( 'cn={0},{1}'.format( name, LDAP_VIRTUE_DN ), tree )

def add_application( id, name, version, os ):

    app = {
        'name': name,
        'version': version,
        'os': os,
        'id': id
    }

    ldap_app = to_ldap( app, 'OpenLDAPapplication' )

    inst.add_obj( ldap_app, 'applications', 'cid', throw_error=True )

def add_resource( id, type, unc, credentials ):

    res = {
        'id': id,
        'type': type,
        'unc': unc,
        'credentials': credentials
    }

    ldap_res = to_ldap( res, 'OpenLDAPresource' )

    inst.add_obj( ldap_res, 'resources', 'cid', throw_error=True )

def add_role( id, name, version, appIds, resIds, transIds ):

    role = {
        'cid': id,
        'name': name,
        'cversion': version,
        'cappIds': str(appIds),
        'cstartResIds': str(resIds),
        'cstartTransIds': str(transIds)
    }

    ldap_role = to_ldap( role, 'OpenLDAProle' )

    inst.add_obj( ldap_role, 'roles', 'cid', throw_error=True )

def add_user( username, authRoleIds ):

    user = {
        'username': username,
        'authorizedRoleIds': str(authRoleIds)
    }

    ldap_user = to_ldap( user, 'OpenLDAPuser' )

    inst.add_obj( ldap_user, 'users', 'cusername', throw_error=True )


if( __name__ == '__main__' ):

    inst = LDAP( '', '' )
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s( dn, 'Test123!' )

    virtue_ou = ldap.modlist.addModlist( {
        'objectClass': ['top', 'organizationalUnit'],
        'ou': 'virtue',
        'description': 'VirtUE organizational unit for binding with AD'
    } )

    inst.conn.add_s( LDAP_VIRTUE_DN, virtue_ou )

    add_subtree( 'applications', 205 )
    add_subtree( 'resources', 206 )
    add_subtree( 'roles', 207 )
    add_subtree( 'transducers', 208 )
    add_subtree( 'users', 209 )
    add_subtree( 'virtues', 210 )

    add_application( 'firefox', 'Firefox', '1.0', 'LINUX' )
    add_application( 'xterm', 'XTerm', '1.0', 'LINUX' )
    add_application( 'thunderbird', 'Thunderbird', '1.0', 'LINUX' )

    add_resource( 'fileshare1', 'DRIVE', '//172.30.1.250/VirtueFileShare', 'token' )

    add_role( 'emptyrole', 'EmptyRole', '1.0', '[]', '[]', '[]' )

    add_user( 'jmitchell', '[]' )
    add_user( 'fpatwa', '[]' )
    add_user( 'klittle', '[]' )
