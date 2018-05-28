#!/usr/bin/python

import argparse

if( __name__ == '__main__' ):
    from test_common import ssh_tool

AMI_ID = 'ami-aa2ea6d0' # Default AMI

def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument( '-i', '--sshkey', type=str, required=True,
                         help='The path to the private key to use ssh with' )
    parser.add_argument( '-e', '--excalibur_server', type=str, required=True,
                         help='The IP address of an existing aws excalibur instance. ' +
                         'If this is set, a new instance will not be created.' )
    parser.add_argument( '--ldap_api', action='store_true', 
                         help='The ldap API Tests' )
    parser.add_argument( '--admin_api', action='store_true', 
                         help='The ADMIN API Tests' )
    parser.add_argument( '--user_api', action='store_true', 
                         help='The USER API Tests' )

    arg = parser.parse_args()

    return arg


if( __name__ == '__main__' ):

    args = parse_args()

    ssh_inst = ssh_tool( 'ubuntu', args.excalibur_server, sshkey=args.sshkey )

    if args.ldap_api:
        ssh_inst.ssh( 'cd galahad/tests/virtue-ci && ./run_ldap_tests.py' )
    if args.admin_api:
        ssh_inst.ssh( 'cd galahad/tests/virtue-ci && ./run_admin_api_tests.py' )
    if args.user_api:
        ssh_inst.ssh( 'cd galahad/tests/virtue-ci && ./run_user_api_tests.py' )
 
    print
    print( 'Success' )
