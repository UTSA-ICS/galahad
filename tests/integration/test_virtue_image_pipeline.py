import json
import os
import shlex
import subprocess
import sys

import boto3
import requests

# For excalibur methods (API, etc)
file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(file_path)) + '/../excalibur'
sys.path.insert(0, base_excalibur_dir)

# For common.py
sys.path.insert(0, '..')

from website.ldaplookup import LDAP
from website.aws import AWS
from assembler.assembler import Assembler
from assembler.stages.core.ssh_stage import SSHStage

sys.path.insert(0, base_excalibur_dir + '/cli')
from sso_login import sso_tool

WORK_DIR = os.getcwd() + '/.tmp_work_dir/'


def setup_module():
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

    assembler_instance = None

    # Create a folder to store test images
    subprocess.check_call(['sudo', 'mkdir', '-p', '/mnt/efs/images/tests'])


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

    # Construction Stage - construct a Unity Image
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
    # Constructor already ran during stack creation, so it must have succeeded.

    # TODO: Mount image
    # TODO: Check for merlin, syslog, auditd, docker, virtue/merlin users,
    #     unity-net, etc (Will probably need help from BBN?)
    pass


def __assemble_applications(unity_image, applications):
    global assembled_image

    assembler = Assembler(work_dir=WORK_DIR)

    # Copy the Unity image for assembly testing into efs/images/tests/
    subprocess.check_call(['sudo', 'cp', '/mnt/efs/images/unities/8GB.img',
                           '/mnt/efs/images/tests/assembly.img'])

    # TODO: Launch on a Valor

    # Get the docker login credentials for communicating with AWS ECR
    docker_login = subprocess.check_output(shlex.split(
        'aws ecr get-login --no-include-email --region us-east-2'))

    # Now check if the server is ready for SSH connections
    stage = SSHStage(valor['guestnet'], '22', WORK_DIR,
                     check_cloudinit=False)
    #stage.run()

    # Assemble the applications specified
    # This will fail because Canvas/Excalibur-to-Virtue networking doesn't work yet.
    #assembler.assemble_running_vm(applications, docker_login,
    #                              valor['guestnet'])

    # TODO: Shutdown the VM

    return app_ami_id


def test_assembler():

    # Update the unity image by adding in the terminal app
    # Run the assumbler for this function.
    #assembled_ami_id = __assemble_application('/mnt/efs/images/unities/8GB.img',
    #                                          ['terminal'])

    role = {
        'name': 'TerminalTestRole',
        'version': '1.0',
        'applicationIds': ['xterm'],
        'startingResourceIds': [],
        'startingTransducerIds': []
    }

    # TODO: Inspect image to assert that assembly added the correct Docker images


def test_provisioner():
    pass


def test_integration_common():
    pass


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
    # TODO: Shutdown any remaining Virtues

    # Cleanup the images created
    subprocess.check_call(['sudo', 'rm', '-rf', '/mnt/efs/images/tests'])
