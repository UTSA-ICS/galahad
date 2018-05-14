#!/usr/bin/python

import os
import sys
import time
import subprocess
import boto3

AMI_ID = 'ami-aa2ea6d0'
SUBNET_ID = 'subnet-00664ce7230870c66'
IAM_NAME = ''

AWS_PUB_KEY = ''
AWS_SECRET_KEY = ''

create_aws_inst = False

def ssh( dns, command, test=True ):

    print
    print
    print "{0}  {1}".format( dns, command )
    print ' '.join( ['ssh', '-i', os.environ['VIRTUE_SSH_ID'], 'ubuntu@' + dns, command] )
    print

    ret = subprocess.call( ['ssh', '-i', os.environ['VIRTUE_SSH_ID'], '-o', 'StrictHostKeyChecking=no', 'ubuntu@' + dns, command] )

    # By default, it is not ok to fail
    if( test ):
        assert ret == 0

    return ret

def scp_to( dns, file_path_local, file_path_remote='', test=True ):

    print
    print
    print "{0}  {1}  {2}".format( dns, file_path_local, file_path_remote )
    print ' '.join( ['scp', '-r', '-i', os.environ['VIRTUE_SSH_ID'], file_path_local, 'ubuntu@' + dns + ':' + file_path_remote] )
    print

    ret = subprocess.call( ['scp', '-r', '-i', os.environ['VIRTUE_SSH_ID'], file_path_local, 'ubuntu@' + dns + ':' + file_path_remote] )

    # By default, it is not ok to fail
    if( test ):
        assert ret == 0

    return ret

def setup_aws_inst( inst_ip ):

    # Install required packages
    ssh( inst_ip, 'sudo apt-get update' )
    #ssh( inst_ip, 'sudo apt-get upgrade -y' )
    ssh( inst_ip, 'sudo apt-get install -y python-pip libldap2-dev libsasl2-dev unzip' )

    # scp openldap/, ldapscripts/, and galahad/
    scp_to( inst_ip, '/home/jeffrey/openldap' )

    # Todo: zip this one... too big
    '''try:
        os.remove( '/tmp/gh.zip' )
    except:
        True
    subprocess.call( ['zip', '-r', '-j', '/tmp/gh.zip', '~/galahad'] )
    scp_to( inst_ip, '/tmp/gh.zip' )
    ssh( inst_ip, 'unzip gh.zip -d .' )'''

    # This takes too long:
    #scp_to( inst_ip, os.environ['VIRTUE_ROOT'] )

    dirs = os.listdir( os.environ['VIRTUE_ROOT'] )

    if( '.git' in dirs ):
        dirs.remove( '.git' )

    ssh( inst_ip, 'mkdir /home/ubuntu/galahad', test=False )
    for x in dirs:
        scp_to( inst_ip, '{0}/{1}'.format( os.environ['VIRTUE_ROOT'], x ), '/home/ubuntu/galahad' )

    # Install and configure slapd
    ssh( inst_ip, 'sudo ~/galahad/tests/virtue-ci/install_ldap.sh' )
    ssh( inst_ip, 'echo \'export LDAPSEARCH="ldapsearch -H ldap://localhost -D cn=admin,dc=canvas,dc=virtue,dc=com -W -b dc=canvas,dc=virtue,dc=com"\' >> ~/.bashrc' )

    # Install required python packages
    ssh( inst_ip, 'sudo pip install --upgrade -r /home/ubuntu/galahad/flask-authlib/requirements.txt' )

    # Setup the schema
    ssh( inst_ip, '~/galahad/tests/virtue-ci/add_canvas_schema.sh' )

    # Create base LDAP structure
    ssh( inst_ip, '~/galahad/tests/virtue-ci/create_base_ldap_structure.py' )

    # Setup AWS client on AWS inst
    ssh( inst_ip, 'sudo apt-get install -y awscli' )
    ssh( inst_ip, 'mkdir .aws', test=False )
    scp_to( inst_ip, os.environ['VIRTUE_ROOT'] + '/tests/virtue-ci/aws_config', '~/.aws/config' )
    scp_to( inst_ip, os.environ['VIRTUE_ROOT'] + '/tests/virtue-ci/aws_credentials', '~/.aws/credentials' )


if( __name__ == '__main__' ):

    if( len(sys.argv) == 1 ):

        # Create AWS inst
        ec2 = boto3.resource('ec2', region_name='us-east-1')

        res = ec2.create_instances( ImageId=AMI_ID,
                                    InstanceType='t2.micro',
                                    KeyName='starlab-virtue-te',
                                    MinCount=1,
                                    MaxCount=1,
                                    Monitoring={'Enabled': False},
                                    SubnetId=SUBNET_ID,
                                    IamInstanceProfile={
                                        'Name': IAM_NAME
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
                                                'Value': 'VirtUE-v3-Ci-Test'
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

        aws_ip = sys.argv[1]

    print( aws_ip )
    
    # Setup the VM
    setup_aws_inst( aws_ip )

    # Run individual tests
    #ssh( aws_ip, 'cd galahad/tests/virtue-ci && ./run_ldap_tests.py' )
    ssh( aws_ip, 'cd galahad/tests/virtue-ci && ./run_admin_api_tests.py' )
    ssh( aws_ip, 'cd galahad/tests/virtue-ci && ./run_user_api_tests.py' )
