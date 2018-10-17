import json
import os
import shlex
import subprocess
import sys
import time

import boto3
import requests

# For excalibur methods (API, etc)
file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(file_path)) + '/../excalibur'
sys.path.insert(0, base_excalibur_dir)

# For common.py
sys.path.insert(0, '..')

from website import ldap_tools
from website.ldaplookup import LDAP
from website.aws import AWS
from assembler.assembler import Assembler
from assembler.stages.core.ssh_stage import SSHStage

sys.path.insert(0, base_excalibur_dir + '/cli')
from sso_login import sso_tool

WORK_DIR = os.getcwd() + '/.tmp_work_dir/'


def setup_module():
    global ami_id
    global app_ami_id
    global assembler_instance

    global session
    global base_url
    global inst

    settings = None
    with open('test_config.json', 'r') as infile:
        settings = json.load(infile)

    excalibur_ip = None
    with open('../setup/excalibur_ip', 'r') as infile:
        excalibur_ip = infile.read().strip() + ':' + settings['port']

    inst = LDAP('', '')
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s(dn, 'Test123!')

    # Connect to Excalibur's REST interface
    redirect = settings['redirect'].format(excalibur_ip)

    sso = sso_tool(excalibur_ip)
    assert sso.login(settings['user'], settings['password'])

    client_id = sso.get_app_client_id(settings['app_name'])
    if (client_id == None):
        client_id = sso.create_app(settings['app_name'], redirect)
        assert client_id

    code = sso.get_oauth_code(client_id, redirect)
    assert code

    token = sso.get_oauth_token(client_id, code, redirect)
    assert 'access_token' in token

    session = requests.Session()
    session.headers = {
        'Authorization': 'Bearer {0}'.format(token['access_token'])
    }
    session.verify = settings['verify']

    base_url = 'https://{0}/virtue/admin'.format(excalibur_ip)

    ami_id = None
    app_ami_id = None
    assembler_instance = None


def __construct_unity():
    global ami_id

    aws = AWS()
    aws_security_group = aws.get_sec_group()
    aws_subnet_id = aws.get_subnet_id()
    #
    build_opts = {
        'env': 'aws',
        'aws_image_id': 'ami-759bc50a',  # Ubuntu 16.04 Xenial
        'aws_instance_type': 't2.micro',
        'aws_security_group': aws_security_group.id,
        'aws_subnet_id': aws_subnet_id,
        'aws_disk_size': 8,
        'create_ami': True
    }

    # Change to the galahad directory to correctly reference the path for
    # various files required during the stages of the constructor.
    os.chdir(os.environ['HOME'] + '/galahad')
    assembler = Assembler()

    # Construction Stage - contrust a Unity Image
    construct = assembler.construct_unity(build_opts, clean=True)

    ami_id = construct[0]
    assert ami_id

    # Now check if the AMI has been successfully created in AWS
    ec2 = boto3.resource('ec2')
    image = ec2.Image(ami_id)

    # Ensure that the image is in a usable state
    image.wait_until_exists(
        Filters=[
            {
                'Name': 'state',
                'Values': ['available']
            }]
    )
    image.reload()
    assert image.state == 'available'

    # Setup the private key used to login to the instance
    private_key = construct[1]
    subprocess.check_call(shlex.split('mkdir -p {}'.format(WORK_DIR)))
    # Write out the key to a file
    with open('{}/id_rsa'.format(WORK_DIR), 'w') as f:
        f.write(private_key)
    subprocess.check_call(shlex.split('chmod 600 {}/id_rsa'.format(WORK_DIR)))

    return ami_id


def test_constructor():
    __construct_unity()


def __assemble_application(unity_image, application):
    global app_ami_id
    global assembler_instance

    aws = AWS()
    aws_security_group = aws.get_sec_group()
    aws_subnet_id = aws.get_subnet_id()
    #
    build_opts = {
        'env': 'aws',
        'aws_image_id': unity_image,  # Unity Image
        'aws_instance_type': 't2.micro',
        'aws_security_group': aws_security_group.id,
        'aws_subnet_id': aws_subnet_id,
        'aws_disk_size': 8
    }

    # Change to the galahad directory to correctly reference the path for
    # various files required during the stages of the constructor.
    os.chdir(os.environ['HOME'] + '/galahad')
    assembler = Assembler(work_dir=WORK_DIR)

    # Start a ec2 instance from the unity image created
    assembler_instance = aws.instance_create(
        image_id=unity_image,
        inst_type='t2.micro',
        subnet_id=aws_subnet_id,
        key_name='starlab-virtue-te',
        tag_key='Project',
        tag_value='Virtue',
        sec_group=aws_security_group.id,
        inst_profile_name='',
        inst_profile_arn=''
    )

    assembler_instance.wait_until_running()
    assembler_instance.reload()

    # Now check if the server is ready for SSH connections
    stage = SSHStage(assembler_instance.public_ip_address, '22', WORK_DIR)
    stage.run()

    # Get the docker login credentials for communicating with AWS ECR
    docker_login = subprocess.check_output(shlex.split(
        'aws ecr get-login --no-include-email --region us-east-2'))

    # Assemble the application specified
    assembler.assemble_running_vm([application], docker_login, assembler_instance.public_ip_address)

    # Create an image of the ec2 instance updated by the assembler
    app_ami_id = assembler.create_aws_ami(assembler_instance)

    assert app_ami_id

    # Now check if the AMI has been successfully created in AWS
    ec2 = boto3.resource('ec2')
    image = ec2.Image(app_ami_id)

    # Ensure that the image is in a usable state
    image.wait_until_exists(
        Filters=[
            {
                'Name': 'state',
                'Values': ['available']
            }]
    )
    image.reload()
    assert image.state == 'available'

    return app_ami_id


def test_role_create():
    global ami_id

    if ami_id == None:
        ami_id = __construct_unity()

    # Update the unity image by adding in the terminal app
    # Run the assumbler for this function.
    assembled_ami_id = __assemble_application(ami_id, 'terminal')

    role = {
        'name': 'TerminalTestRole',
        'version': '1.0',
        'applicationIds': ['xterm'],
        'startingResourceIds': [],
        'startingTransducerIds': []
    }

    response = session.get(
        base_url + '/role/create',
        params={'role': json.dumps(role),
                'ami_id': assembled_ami_id
                }
    )

    print(response.json())
    assert set(response.json().keys()) == set(['id', 'name'])

    role_id = response.json()['id']

    role = inst.get_obj('cid', role_id, objectClass='OpenLDAProle', throw_error=True)
    assert role != ()
    ldap_tools.parse_ldap(role)
    assert role['amiId'][0:4] == 'ami-'

    test_virtue = inst.get_obj('croleId', role_id,
                               objectClass='OpenLDAPvirtue', throw_error=True)

    i = 0
    while (test_virtue == () and i < 120):
        time.sleep(1)
        test_virtue = inst.get_obj(
            'croleId', role_id, objectClass='OpenLDAPvirtue', throw_error=True
        )
        i = i + 1
    assert test_virtue != ()

    ldap_tools.parse_ldap(test_virtue)
    assert test_virtue['username'] == 'NULL'
    assert test_virtue['applicationIds'] == []
    assert test_virtue['awsInstanceId'][0:2] == 'i-'

    aws = AWS()
    test_virtue = aws.populate_virtue_dict(test_virtue)
    assert test_virtue['state'] in aws.aws_state_to_virtue_state.values()

    aws.instance_destroy(test_virtue['awsInstanceId'], block=False)
    inst.del_obj('cid', test_virtue['id'], objectClass='OpenLDAPvirtue',
                 throw_error=True)


def __delete_ami_and_snapshot(ami_id):
    ec2 = boto3.resource('ec2')
    image = ec2.Image(ami_id)

    # Find the snapshot assoicated with the AMI
    snapshot_id = image.block_device_mappings[0]['Ebs']['SnapshotId']

    # Deregister the AMI
    image.deregister()

    # Delete the snapshot
    ec2 = boto3.client('ec2')
    ec2.delete_snapshot(SnapshotId=snapshot_id)


def teardown_module():
    # Terminate the instances created
    if assembler_instance != None:
        assembler_instance.terminate()

    # Cleanup the AMIs created
    if ami_id != None:
        __delete_ami_and_snapshot(ami_id)

    if app_ami_id != None:
        __delete_ami_and_snapshot(app_ami_id)
