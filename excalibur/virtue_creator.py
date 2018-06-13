#!/usr/bin/python

import sys
import random
from website.ldaplookup import LDAP
#from website.aws.aws import AWS


if( __name__ == '__main__' ):
    action = sys.argv[1]
    ip = sys.argv[2]

    role_id = 'Test'
    username = 'NULL'

    if( len( sys.argv ) > 3 ):
        role_id = sys.argv[3]
    if( len( sys.argv ) > 4 ):
        username = sys.argv[4]

    #aws = AWS()

    ldap = LDAP( '', '' )
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    ldap.get_ldap_connection()
    ldap.conn.simple_bind_s( dn, 'Test123!' )

    if( action == 'create' ):

        #vm = aws.instance_create()
        virtue = {'cid': str(random.randint( 0, 1023 )),
                  'cusername': username,
                  'croleId': role_id,
                  'cappIds': '[]',
                  'cresIds': '[]',
                  'ctransIds': '[]',
                  'cstate': 'STOPPED',#vm.state['Name'],
                  'cipAddress': ip,
                  'objectClass': 'OpenLDAPvirtue',
                  'ou': 'Virtue' }

        ret = ldap.add_obj( virtue, 'virtues', 'cid' )
        print( 'Return value: {0}'.format(ret) )

    elif( action == 'destroy' ):

        #inst_id = AWS.get_id_from_ip( ip )
        #print( 'inst_id = {0}'.format( inst_id ) )

        #aws.instance_destroy( inst_id )

        ret = ldap.del_obj( 'cipAddress', ip, objectClass='OpenLDAPvirtue' )
        print( 'Return value: {0}'.format(ret) )
    else:
        print( 'Usage: ./{0} <action> <ip> <role> <username>'.format( sys.argv[0] ) )
