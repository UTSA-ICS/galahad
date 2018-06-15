#!/usr/bin/python

import argparse

if( __name__ == '__main__' ):
    import setup
    from test_common import ssh_tool

AMI_ID = 'ami-aa2ea6d0' # Default AMI

def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument( '-i', '--sshkey', type=str, required=True,
                         help='The path to the private key to use ssh with' )
    parser.add_argument( '-k', '--awskeys', type=str, required=True,
                         help='Path to the AWS credentials for the ec2 instance to use' )
    parser.add_argument( '-g', '--github_key', type=str, required=True,
                         help='Path to a private ssh key to clone the github ' +
                         'repo on the ec2 instance' )
    parser.add_argument( '-m', '--iamname', type=str, required=False, default='',
                         help='The AWS IAM name to use while creating the ec2 instance' )
    parser.add_argument( '-I', '--ip', type=str, required=False,
                         help='The IP address of an existing ec2 instance. ' +
                         'If this is set, a new instance will not be created.' )
    parser.add_argument( '-a', '--ami', type=str, required=False, default=AMI_ID,
                         help='The AMI ID to create the ec2 instance with' )
    parser.add_argument( '-s', '--subnet', type=str, required=False,
                         help='The subnet ID to use while creating the ec2 instance' )
    parser.add_argument( '-n', '--name', type=str, required=False, default='',
                         help='The name for the ec2 instance' )
    parser.add_argument( '-u', '--username', type=str, required=False, default='ubuntu',
                         help='The username with which to ssh into the ec2 instance' )
    parser.add_argument( '-b', '--branch', type=str, required=False, default='master',
                         help='The branch name to checkout on the Excalibur VM' )

    arg = parser.parse_args()

    return arg


if( __name__ == '__main__' ):

    args = parse_args()

    if( args.ip == None ):
        key_name = '.'.join( args.sshkey.split('/')[-1].split('.')[0:-1] )

        aws_ip = setup.create_aws_inst( args.ami, args.subnet, args.iamname, args.name, key_name )
    else:
        aws_ip = args.ip

    print( aws_ip )

    ssh_inst = ssh_tool( args.username, aws_ip, sshkey=args.sshkey )

    # Setup the VM
    setup.setup_aws_inst( ssh_inst, args.github_key, args.awskeys, args.branch )

    # Run individual tests
    ssh_inst.ssh( 'cd galahad/tests/unit && pytest test_ldap.py' )
    ssh_inst.ssh( 'cd galahad/tests/unit && pytest test_admin_api.py' )
    ssh_inst.ssh( 'cd galahad/tests/unit && pytest test_user_api.py' )
    ssh_inst.ssh( 'cd galahad/tests/unit && pytest test_aws.py' )

    print
    print( 'Success' )
