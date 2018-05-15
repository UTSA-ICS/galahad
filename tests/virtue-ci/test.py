#!/usr/bin/python

import os
import sys
import time
import subprocess
import boto3
import argparse

AMI_ID = 'ami-aa2ea6d0' # Default AMI

def ssh( dns, command, test=True ):

    print
    print
    print "{0}  {1}".format( dns, command )
    print ' '.join( ['ssh', '-i', args.sshkey, args.username + '@' + dns, command] )
    print

    ret = subprocess.call( ['ssh', '-i', args.sshkey, '-o', 'StrictHostKeyChecking=no', args.username + '@' + dns, command] )

    # By default, it is not ok to fail
    if( test ):
        assert ret == 0

    return ret

def scp_to( dns, file_path_local, file_path_remote='', test=True ):

    print
    print
    print "{0}  {1}  {2}".format( dns, file_path_local, file_path_remote )
    print ' '.join( ['scp', '-r', '-i', args.sshkey, file_path_local, args.username + '@' + dns + ':' + file_path_remote] )
    print

    ret = subprocess.call( ['scp', '-r', '-i', args.sshkey, file_path_local, args.username + '@' + dns + ':' + file_path_remote] )

    # By default, it is not ok to fail
    if( test ):
        assert ret == 0

    return ret

def setup_aws_inst( inst_ip ):

    # Install required packages
    ssh( inst_ip, 'sudo apt-get update' )
    #ssh( inst_ip, 'sudo apt-get upgrade -y' )
    ssh( inst_ip, 'sudo apt-get install -y python-pip libldap2-dev libsasl2-dev unzip' )

    # scp galahad/
    dirs = os.listdir( os.environ['VIRTUE_ROOT'] )

    if( '.git' in dirs ):
        dirs.remove( '.git' )

    ssh( inst_ip, 'mkdir ~/galahad', test=False )
    for x in dirs:
        scp_to( inst_ip, '{0}/{1}'.format( os.environ['VIRTUE_ROOT'], x ), '~/galahad' )

    # Install and configure slapd
    ssh( inst_ip, 'sudo ~/galahad/tests/virtue-ci/install_ldap.sh' )
    ssh( inst_ip, 'echo \'export LDAPSEARCH="ldapsearch -H ldap://localhost -D cn=admin,dc=canvas,dc=virtue,dc=com -W -b dc=canvas,dc=virtue,dc=com"\' >> ~/.bashrc' )

    # Install required python packages
    ssh( inst_ip, 'sudo pip install --upgrade -r ~/galahad/flask-authlib/requirements.txt' )

    # Setup the schema
    ssh( inst_ip, '~/galahad/tests/virtue-ci/add_canvas_schema.sh' )

    # Create base LDAP structure
    ssh( inst_ip, '~/galahad/tests/virtue-ci/create_base_ldap_structure.py' )

    # Setup AWS client on AWS inst
    ssh( inst_ip, 'sudo apt-get install -y awscli' )
    ssh( inst_ip, 'mkdir .aws', test=False )
    scp_to( inst_ip, os.environ['VIRTUE_ROOT'] + '/tests/virtue-ci/aws_config', '~/.aws/config' )
    scp_to( inst_ip, args.awskeys, '~/.aws/credentials' )

def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument( '-i', '--sshkey', type=str, required=True,
                         help='The path to the private key to use ssh with' )
    parser.add_argument( '-k', '--awskeys', type=str, required=True,
                         help='Path to the AWS credentials for the ec2 instance to use' )
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

    arg = parser.parse_args()

    return arg


if( __name__ == '__main__' ):

    args = parse_args()

    if( args.ip == None ):

        if( args.subnet == None ):
            print( 'Need subnet value -s' )
            exit()

        # Get the name of the key file without the .pem file extension
        key_name = '.'.join( args.sshkey.split('/')[-1].split('.')[0:-1] )

        # Create AWS inst
        ec2 = boto3.resource('ec2', region_name='us-east-1')

        res = ec2.create_instances( ImageId=args.ami,
                                    InstanceType='t2.micro',
                                    KeyName=key_name,
                                    MinCount=1,
                                    MaxCount=1,
                                    Monitoring={'Enabled': False},
                                    SubnetId=args.subnet,
                                    IamInstanceProfile={
                                        'Name': args.iamname
                                    },
                                    TagSpecifications=[
                                        {
                                            'ResourceType': 'instance',
                                            'Tags': [{
                                                'Key': 'Project',
                                                'Value': 'Virtue'
                                            },
                                            {
                                                'Key': 'Name',
                                                'Value': args.name
                                            }]
                                        },
                                        {
                                            'ResourceType': 'volume',
                                            'Tags': [{
                                                'Key': 'Project',
                                                'Value': 'Virtue'
                                            }]
                                        }
                                    ] )

        instance = res[0]
        instance.wait_until_running()
        time.sleep(5)
        instance.reload()

        print( instance.id )

        aws_ip = instance.public_ip_address

    else:

        aws_ip = args.ip

    print( aws_ip )
    
    # Setup the VM
    setup_aws_inst( aws_ip )

    # Run individual tests
    ssh( aws_ip, 'cd galahad/tests/virtue-ci && ./run_ldap_tests.py' )
    ssh( aws_ip, 'cd galahad/tests/virtue-ci && ./run_admin_api_tests.py' )
    ssh( aws_ip, 'cd galahad/tests/virtue-ci && ./run_user_api_tests.py' )

    print
    print( 'Success' )
