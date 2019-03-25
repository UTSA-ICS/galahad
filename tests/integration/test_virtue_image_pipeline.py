# Copyright (c) 2019 by Star Lab Corp.

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

EXCALIBUR_HOSTNAME = 'excalibur.galahad.com'

def setup_module():
    global assembler_instance

    global session
    global base_url
    global inst

    settings = None
    with open('test_config.json', 'r') as infile:
        settings = json.load(infile)

    excalibur_ip = EXCALIBUR_HOSTNAME + ':' + settings['port']

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
