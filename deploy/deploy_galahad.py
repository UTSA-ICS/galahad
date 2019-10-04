#!/usr/bin/python3

# Copyright (c) 2019 by Star Lab Corp.


import argparse
import json
import logging
import os
import subprocess
import sys
import threading
import time
from pprint import pformat

import boto3
from sultan.api import Sultan, SSHConfig

# File names
STACK_TEMPLATE = 'setup/galahad-stack.yaml'
AWS_INSTANCE_INFO = '../tests/aws_instance_info.json'

# Directories for key storage
GALAHAD_KEY_DIR_NAME = 'galahad-keys'
GALAHAD_KEY_DIR = '/mnt/efs/galahad-keys'
GALAHAD_CONFIG_DIR = '~/galahad-config'
USER_KEY_DIR = '~/user-keys'

# Node addresses
EXCALIBUR_HOSTNAME = 'excalibur.galahad.com'
RETHINKDB_HOSTNAME = 'rethinkdb.galahad.com'
AGGREGATOR_HOSTNAME = 'aggregator.galahad.com'
VALOR_ROUTER_HOSTNAME = 'valor-router.galahad.com'
XEN_PVM_BUILDER_HOSTNAME = 'xenpvmbuilder.galahad.com'
CANVAS_HOSTNAME = 'canvas.galahad.com'

# Configure the Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_ssh_cmd(host_server, sshkey, cmd):
    config = SSHConfig(
        identity_file=sshkey,
        option='StrictHostKeyChecking=no')

    with Sultan.load(
            user='ubuntu',
            hostname=host_server,
            ssh_config=config) as s:

        result = eval('s.{}.run()'.format(cmd))

        if result.is_success:
            logger.info('success: {}'.format(result.is_success))

        else:
            print(result.stderr)
            logger.info('\nstdout: {}\nstderr: {}\nsuccess: {}'.format(
                pformat(result.stdout),
                pformat(result.stderr),
                pformat(result.is_success)))

        assert result.rc == 0

        return result


def check_cloud_init_finished(host_server, sshkey):
    # Check if the file "/var/lib/cloud/instance/boot-finished" exists
    # indicating that boot is complete and cloud init has finished running
    _cmd = '''bash(('-c "while [ ! -f /var/lib/cloud/instance/boot-finished ];'
                       'do echo \\\\\"Cloud init has not finished\\\\\";sleep 5;done;'
                       'echo \\\\\"Cloud init has now finished\\\\\""'))'''
    run_ssh_cmd(host_server, sshkey, _cmd)


# This should be subclassed. It is not meant to be used on its own.
class Instance:

    def checkout_repo(self, repo, branch='master'):
        # Cleanup any left over repos
        run_ssh_cmd(self.ip_address, self.ssh_key, "rm('-rf {}')".format(repo))
        #
        if branch == 'master':
            _cmd = "git('clone https://gitlab.com/utsa-ics/galahad/{}.git')".format(repo)
        else:
            _cmd = "git('clone https://gitlab.com/utsa-ics/galahad/{}.git -b {}')".format(
                repo, branch)
        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd)

    def copy_config(self, config_path):
        run_ssh_cmd(self.ip_address, self.ssh_key, "rm('-rf {}')".format(config_path))
        with Sultan.load() as s:
            s.scp(
                '-r -o StrictHostKeyChecking=no -i {} {} ubuntu@{}:{} '.
                format(self.ssh_key, config_path, self.ip_address, config_path)).run()

    def shutdown(self):
        _cmd = "sudo('shutdown -h 1')"
        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd)


class Stack:

    def read_template(self):

        file = open(self.stack_template, "r")

        return file.read()

    def setup_stack(self, stack_template, stack_name, suffix_value, key_name,
                    import_stack_name='None'):

        self.stack_template = stack_template
        self.stack_name = stack_name
        self.suffix_value = suffix_value

        client = boto3.client('cloudformation')
        stack = client.create_stack(
            StackName=self.stack_name,
            TemplateBody=self.read_template(),
            Parameters=[{
                'ParameterKey': 'KeyName',
                'ParameterValue': key_name
            }, {
                'ParameterKey': 'NameSuffix',
                'ParameterValue': self.suffix_value
            }, {
                'ParameterKey': 'ImportStackName',
                'ParameterValue': import_stack_name
            }])

        logger.info('Starting up Stack [{}] ...'.format(self.stack_name))
        waiter = client.get_waiter('stack_create_complete')
        waiter.wait(StackName=self.stack_name)

        # Log the events of the Stack
        response = client.describe_stack_events(StackName=self.stack_name)

        for event in response['StackEvents']:
            if 'CREATE_COMPLETE' in event['ResourceStatus']:
                logger.info('{} {} {}'.format(
                    event['Timestamp'],
                    event['ResourceType'],
                    event['ResourceStatus']))

        # Wait a min to Ensure that the Stack resources are completely online.
        time.sleep(60)

        return stack

    def delete_stack(self, stack_name):

        self.stack_name = stack_name
        #
        client = boto3.client('cloudformation')
        self.clear_security_groups()
        self.terminate_non_stack_instances(stack_name)
        response = client.delete_stack(StackName=stack_name)
        waiter = boto3.client('cloudformation').get_waiter(
            'stack_delete_complete')
        waiter.wait(StackName=self.stack_name)

        return response

    def clear_security_groups(self):

        client = boto3.client('ec2')
        security_groups = client.describe_security_groups(
            Filters=[{
                'Name': 'tag-key',
                'Values': ['aws:cloudformation:stack-name']
            }, {
                'Name': 'tag-value',
                'Values': [self.stack_name]
            }])
        ec2 = boto3.resource('ec2')
        for group in security_groups['SecurityGroups']:
            sec_group = ec2.SecurityGroup(group['GroupId'])
            if sec_group.ip_permissions:
                sec_group.revoke_ingress(
                    IpPermissions=sec_group.ip_permissions)
            if sec_group.ip_permissions_egress:
                sec_group.revoke_egress(
                    IpPermissions=sec_group.ip_permissions_egress)

    def terminate_non_stack_instances(self, stack_name):
        # Find the VPC ID from the excalibur Instance
        client = boto3.client('ec2')
        server = client.describe_instances(
            Filters=[{
                'Name': 'tag:aws:cloudformation:logical-id',
                'Values': ['ExcaliburServer']
            }, {
                'Name': 'tag:aws:cloudformation:stack-name',
                'Values': [stack_name]
            }])

        try:
            vpc_id = server['Reservations'][0]['Instances'][0]['VpcId']
        except:
            logger.error("Unable to find VPC ID from instance Excalibur")
            raise

        # Now find all instances in ec2 within the VPC but without the stack tags.
        ec2 = boto3.client('ec2')

        # Get ALL instances in the stack VPC
        vms = ec2.describe_instances(Filters=[{'Name': 'vpc-id',
                                               'Values': [vpc_id]}])
        instances_not_in_stack = []
        for vm in vms['Reservations']:
            if 'aws:cloudformation:stack-name' not in str(vm['Instances'][0]['Tags']):
                instances_not_in_stack.append(vm['Instances'][0]['InstanceId'])

        # Now Terminate these instances not created by the stack
        resource = boto3.resource('ec2')
        for instance in instances_not_in_stack:
            resource.Instance(instance).terminate()
            logger.info('Terminating instance [{}] not created by the stack'.format(instance))

    def list_stacks(self):
        client = boto3.client('cloudformation')
        response = client.list_stacks()
        for stack in response['StackSummaries']:
            if 'UPDATE' in stack['StackStatus'] or 'CREATE' in stack['StackStatus']:
                logger.info('{} {} {}'.format(
                    stack['StackName'],
                    stack['CreationTime'],
                    stack['StackStatus']))


class RethinkDB(Instance):

    def __init__(self, stack_name, ssh_key):

        self.stack_name = stack_name
        self.ssh_key = ssh_key
        self.ip_address = RETHINKDB_HOSTNAME

    def setup(self, branch):

        # Ensure that cloud init has finished
        check_cloud_init_finished(self.ip_address, self.ssh_key)

        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/rethinkdb.conf'.
                format(self.ssh_key, 'setup/rethinkdb.conf', self.ip_address)).run()
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/setup_rethinkdb.sh'.
                format(self.ssh_key, 'setup/setup_rethinkdb.sh', self.ip_address)).run()
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/configure_rethinkdb.py'.
                format(self.ssh_key, 'setup/configure_rethinkdb.py', self.ip_address)).run()

        logger.info(
            'Now checking out relevant excalibur repos for {} branch'.format(
                branch))
        # Check out galahad repos required for rethinkdb
        self.copy_config('~/galahad-config')

        _cmd1 = "bash('./setup_rethinkdb.sh')"

        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd1)


class Excalibur(Instance):

    def __init__(self, stack_name, ssh_key):

        self.stack_name = stack_name
        self.ssh_key = ssh_key
        self.ip_address = EXCALIBUR_HOSTNAME
        self.vpc_id = None
        self.subnet_id = None
        self.default_security_group_id = None
        self.update_aws_info()

    def update_aws_info(self):

        client = boto3.client('ec2')
        server = client.describe_instances(
            Filters=[{
                'Name': 'tag:aws:cloudformation:logical-id',
                'Values': ['ExcaliburServer']
            }, {
                'Name': 'tag:aws:cloudformation:stack-name',
                'Values': [self.stack_name]
            }, {
                'Name': 'instance-state-name',
                'Values': ['running']
            }])

        self.vpc_id = server['Reservations'][0]['Instances'][0]['VpcId']

        self.subnet_id = server['Reservations'][0]['Instances'][0]['SubnetId']

        for group in server['Reservations'][0]['Instances'][0]['SecurityGroups']:
            if group['GroupName'] == 'default':
                self.default_security_group_id = group['GroupId']

    def setup_aws_access(self, aws_config, aws_keys):
        run_ssh_cmd(self.ip_address, self.ssh_key, "mkdir('~/.aws')")
        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/.aws/config '.
                format(self.ssh_key, aws_config, self.ip_address)).run()
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/.aws/credentials '.
                format(self.ssh_key, aws_keys, self.ip_address)).run()

    def setup(self, branch, aws_config, aws_keys, key_name):

        # Ensure that cloud init has finished
        check_cloud_init_finished(self.ip_address, self.ssh_key)

        logger.info('Setting up key for github access')
        # Transfer the private key to the server to enable
        # it to access github without being prompted for credentials
        logger.info(
            'Now checking out relevant excalibur repos for {} branch'.format(
                branch))
        # Check out galahad repos required for excalibur
        self.copy_config('~/galahad-config')
        self.checkout_repo('galahad', branch)

        # Sleep for 10 seconds to ensure that both repos are completely checked out
        time.sleep(10)

        # Setup the config and keys for AWS communication
        self.setup_aws_access(aws_config, aws_keys)

        # Call the setup_excalibur.sh script for system and pip packages.
        _cmd1 = "cd('galahad/deploy/setup').and_().bash('./setup_excalibur.sh')"
        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd1)

        # Call the setup_ldap.sh script for openldap installation and config.
        _cmd2 = "cd('galahad/deploy/setup').and_().bash('./setup_ldap.sh')"
        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd2)

        # Call the setup_bft.sh script for Blue Force Tracker installation and config.
        _cmd2 = "cd('galahad/deploy/setup').and_().bash('./setup_bft.sh')"
        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd2)

        self.setup_aws_instance_info(key_name)

        # Setup the transducer heartbeat Listener and Start it
        _cmd3 = "cd('galahad/transducers').and_().bash('./install_heartbeatlistener.sh')"
        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd3)

        # Start the flask-server (excalibur)
        _cmd4 = "cd('galahad/excalibur').and_().bash('./start-screen.sh')"
        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd4)

        # Wait a min to Ensure that Excalibur setup is complete
        time.sleep(60)

        # Now populate the /var/private/ssl dir for excalibur
        EXCALIBUR_PRIVATE_DIR = '/var/private/ssl'
        _cmd6 = "sudo('mkdir -p {0}').and_().sudo('chown -R ubuntu.ubuntu /var/private')".format(EXCALIBUR_PRIVATE_DIR)
        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd6)
        _cmd6 = "cp('{0}/excalibur_private_key.pem {1}/')".format(GALAHAD_CONFIG_DIR, EXCALIBUR_PRIVATE_DIR)
        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd6)
        _cmd6 = "cp('{0}/rethinkdb_keys/rethinkdb_cert.pem {1}/')".format(GALAHAD_CONFIG_DIR, EXCALIBUR_PRIVATE_DIR)
        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd6)
        _cmd6 = "cp('-r {0}/elasticsearch_keys {1}/')".format(GALAHAD_CONFIG_DIR, EXCALIBUR_PRIVATE_DIR)
        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd6)

        # Setup the EFS mount and populate Valor config files
        _cmd7 = "cd('galahad/deploy/setup').and_().bash('./setup_efs.sh')"
        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd7)

        # Setup the Default key to be able to login to the virtues
        # This private key's corresponding public key will be used for the virtues
        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {0} {0} ubuntu@{1}:{2}/default-virtue-key.pem'.
                format(self.ssh_key, self.ip_address, USER_KEY_DIR)).run()

        # Start the Blue Force Tracker
        _cmd8 = "cd('galahad/blue_force_track').and_().bash('./start_bft.sh')"
        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd8)

    def setup_aws_instance_info(self, key_name):
        aws_instance_info = {}
        aws_instance_info['image_id'] = 'ami-aa2ea6d0'
        aws_instance_info['inst_type'] = 't2.micro'
        aws_instance_info['subnet_id'] = self.subnet_id
        aws_instance_info['key_name'] = key_name
        aws_instance_info['tag_key'] = 'Project'
        aws_instance_info['tag_value'] = 'Virtue'
        aws_instance_info['sec_group'] = self.default_security_group_id
        aws_instance_info['inst_profile_name'] = ''
        aws_instance_info['inst_profile_arn'] = ''

        # Now write this to a file
        filename = AWS_INSTANCE_INFO.split('/')[-1]
        with open('/tmp/{0}'.format(filename), 'w') as f:
            json.dump(aws_instance_info, f)

        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {0} /tmp/{1} ubuntu@{2}:~/galahad/deploy/{3}'.
                format(self.ssh_key, filename, self.ip_address, AWS_INSTANCE_INFO)).run()

        return aws_instance_info


class Aggregator(Instance):

    def __init__(self, stack_name, ssh_key):

        self.stack_name = stack_name
        self.ssh_key = ssh_key
        self.ip_address = AGGREGATOR_HOSTNAME

    def setup(self, branch):

        # Ensure that cloud init has finished
        check_cloud_init_finished(self.ip_address, self.ssh_key)

        logger.info(
            'Now checking out relevant excalibur repos for {} branch'.format(
                branch))
        # Check out galahad-config repo required for the certs
        self.copy_config('~/galahad-config')

        _cmd1 = "cd('docker-virtue/elastic').and_().bash('./elastic_setup.sh')"

        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd1)


class EFS:

    def __init__(self, stack_name, ssh_key):

        self.stack_name = stack_name
        self.ssh_key = ssh_key
        self.efs_id = self.get_efs_id()

    def get_efs_id(self):
        cloudformation = boto3.resource('cloudformation')
        EFSStack = cloudformation.Stack(self.stack_name)

        for output in EFSStack.outputs:
            if output['OutputKey'] == 'FileSystemID':
                efs_id = output['OutputValue']

        efs_id = '{}.efs.us-east-1.amazonaws.com'.format(efs_id)
        logger.info('EFS File System ID is {}'.format(efs_id))

        return efs_id

    def setup_valor_router(self):
        # SCP over the setup file to the instance
        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {} ../valor/{} ubuntu@{}:~/.'.
                format(self.ssh_key, 'setup_valor_router.sh', VALOR_ROUTER_HOSTNAME)).run()

        # Execute the setup file on the instance
        _cmd = "bash('./setup_valor_router.sh')"
        run_ssh_cmd(VALOR_ROUTER_HOSTNAME, self.ssh_key, _cmd)

    def setup_valor_keys(self):
        # Generate private/public keypair for valor nodes to be able to access each other.
        _cmd = "cd('/mnt/efs/{}').and_().ssh__keygen('-P \"\" -f valor-key')".format(GALAHAD_KEY_DIR_NAME)
        run_ssh_cmd(EXCALIBUR_HOSTNAME, self.ssh_key, _cmd)

    def setup_xen_pvm_builder(self):

        # Ensure that cloud init has finished
        check_cloud_init_finished(XEN_PVM_BUILDER_HOSTNAME, self.ssh_key)

        # scp workaround payload to node
        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {} setup/xm.tmpl ubuntu@{}:~/.'.
                format(self.ssh_key, XEN_PVM_BUILDER_HOSTNAME)).run()
            s.scp(
                ('-o StrictHostKeyChecking=no -i {} '
                 'setup/sources.list ubuntu@{}:~/.').
                format(self.ssh_key, XEN_PVM_BUILDER_HOSTNAME)).run()
            s.scp(
                ('-o StrictHostKeyChecking=no -i {} '
                 'setup/setup_base_ubuntu_pvm.sh ubuntu@{}:~/.').
                format(self.ssh_key, XEN_PVM_BUILDER_HOSTNAME)).run()
            s.scp(
                ('-o StrictHostKeyChecking=no -i {} '
                 'setup/setup_ubuntu_image.sh ubuntu@{}:~/.').
                format(self.ssh_key, XEN_PVM_BUILDER_HOSTNAME)).run()

        # Apply workarounds and setup the xen pvm builder server
        ssh_cmd = "bash('setup_base_ubuntu_pvm.sh')"
        run_ssh_cmd(XEN_PVM_BUILDER_HOSTNAME, self.ssh_key, ssh_cmd)

    def setup_ubuntu_img(self, image_name):
        # Create the base ubuntu image
        ssh_cmd = "bash('setup_ubuntu_image.sh {0}')".format(image_name)
        run_ssh_cmd(XEN_PVM_BUILDER_HOSTNAME, self.ssh_key, ssh_cmd)

    def shutdown_xen_pvm_builder(self):
        # TODO Another method will need to be added to start the instance

        _shutdown_cmd = "sudo('shutdown -h 1')"
        run_ssh_cmd(XEN_PVM_BUILDER_HOSTNAME, self.ssh_key, _shutdown_cmd)

    def setup_unity_img(self, constructor_ip, image_name):

        pub_key = subprocess.run(['ssh-keygen', '-y', '-f', self.ssh_key],
                                 stdout=subprocess.PIPE).stdout

        pub_key_cmd = '''bash('-c "echo {0} > /tmp/{1}_unity_key.pub"')'''.format(
            pub_key.decode().strip(), image_name.split('.')[0])
        run_ssh_cmd(constructor_ip, self.ssh_key, pub_key_cmd)

        # Construct Unity
        construct_cmd = '''sudo(('python galahad/excalibur/call_constructor.py'
                                 ' -b /mnt/efs/images/base_ubuntu/{0}'
                                 ' -p /tmp/{1}_unity_key.pub'
                                 ' -o /mnt/efs/images/unities/{0}'
                                 ' -w /mnt/efs/{1}_tmp'))'''.format(
            image_name,
            image_name.split('.')[0])
        run_ssh_cmd(constructor_ip, self.ssh_key, construct_cmd)


class Canvas(Instance):

    def __init__(self, stack_name, ssh_key):

        self.stack_name = stack_name
        self.ssh_key = ssh_key
        self.ip_address = CANVAS_HOSTNAME

    def setup(self, branch):

        # Ensure that cloud init has finished
        check_cloud_init_finished(self.ip_address, self.ssh_key)

        logger.info(
            'Now checking out relevant galahad repos for {} branch'.format(
                branch))
        # Check out galahad-config repo required for the certs
        self.checkout_repo('galahad', branch)

        _cmd1 = "cd('galahad/deploy/setup').and_().bash('./setup_canvas.sh')"

        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd1)

        # Shutdown the node to reduce cost. It can be started up for testing.
        self.shutdown()


class StandbyPools:

    def __init__(self, stack_name, ssh_key):

        self.stack_name = stack_name
        self.ssh_key = ssh_key
        self.server_ip = EXCALIBUR_HOSTNAME

    def initialize_valor_standby_pool(self):

        _cmd = "cd('galahad/deploy/setup').and_().python(" \
               "'create_standby_pools.py --valors')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

    def initialize_role_image_file_standby_pool(self, unity_image_size):

        _cmd = "cd('galahad/deploy/setup').and_().python(" \
               "'create_standby_pools.py --role_image_files " \
               "--unity_image_size {}')".format(unity_image_size)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)


class AutomatedVirtueMigration:

    def __init__(self, stack_name, ssh_key):
        self.stack_name = stack_name
        self.ssh_key = ssh_key
        self.server_ip = EXCALIBUR_HOSTNAME

    def activate_automated_virtue_migration(self, migration_interval):
        username = "slapd@virtue.gov"
        password = "Test123!"
        _cmd = "cd('galahad/deploy/setup').and_().bash('./automated_virtue_migration.sh " \
               "{0} {1} {2}')".format(username, password, migration_interval)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)


def create_and_setup_image_unity_files(stack_name, sshkey, image_size):
    efs = EFS(stack_name, sshkey)

    # Create a base ubuntu image
    start_ubuntu_img_time = time.time()
    efs.setup_ubuntu_img(image_size)
    logger.info(
        '\n*** Time taken for {0} ubuntu img is [{1}] ***\n'.format(image_size,
                                                                    (time.time() - start_ubuntu_img_time) / 60))

    # Build a unity from the base ubuntu image
    start_unity_time = time.time()
    efs.setup_unity_img(EXCALIBUR_HOSTNAME, image_size + '.img')
    logger.info(
        '\n*** Time taken for {0} unity is [{1}] ***\n'.format(image_size,
                                                               (time.time() - start_unity_time) / 60))

    # Create Standby Pool of role image files
    standby_pools = StandbyPools(stack_name, sshkey)
    start_standby_role_pools_time = time.time()
    standby_pools.initialize_role_image_file_standby_pool(image_size)
    logger.info(
        '\n*** Time taken for Standby Pool for image {0} is [{1}] ***\n'.format(
            image_size, (time.time() - start_standby_role_pools_time) / 60))

    logger.info(
        '\n*** Total Time taken for image {0} is [{1}] ***\n'.format(
            image_size, (time.time() - start_ubuntu_img_time) / 60))


def setup(sshkey, stack_name, stack_suffix, import_stack_name, aws_config,
          aws_keys, branch, image_size, deactivate_virtue_migration,
          auto_migration_interval, key_name):

    start_stack_time = time.time()

    stack = Stack()
    stack.setup_stack(STACK_TEMPLATE, stack_name, stack_suffix, key_name,
                      import_stack_name)
    logger.info('\n*** Time taken for Stack Creation is [{}] ***\n'.format(
        (time.time() - start_stack_time) / 60))

    start_setup_time = time.time()

    start_xen_pvm_time = time.time()
    efs = EFS(stack_name, sshkey)
    efs.setup_xen_pvm_builder()
    logger.info('\n*** Time taken for Xen PVM Setup is [{}] ***\n'.format(
        (time.time() - start_xen_pvm_time) / 60))

    start_excalibur_time = time.time()
    excalibur = Excalibur(stack_name, sshkey)
    excalibur.setup(branch, aws_config, aws_keys, key_name)
    logger.info('\n*** Time taken for excalibur is [{}] ***\n'.format(
        (time.time() - start_excalibur_time) / 60))

    # Start Creation of base ubuntu, Unity and Standby role image files
    create_img_file_threads = []
    for image in image_size:
        create_img_file_start_time = time.time()
        create_img_file_thread = threading.Thread(
            target=create_and_setup_image_unity_files, name=image,
            args=(stack_name, sshkey, image,))
        create_img_file_thread.start()
        create_img_file_threads.append(
            {"image_size": image, "start_time": create_img_file_start_time,
                "thread": create_img_file_thread})

    start_aggregator_time = time.time()
    aggregator = Aggregator(stack_name, sshkey)
    aggregator_thread = threading.Thread(target=aggregator.setup, name="aggregator",
                                         args=(branch,))
    aggregator_thread.start()

    canvas = Canvas(stack_name, sshkey)
    canvas_thread = threading.Thread(target=canvas.setup, name="canvas",
                                     args=(branch,))
    canvas_thread.start()

    start_rethinkdb_time = time.time()
    rethinkdb = RethinkDB(stack_name, sshkey)
    rethinkdb.setup(branch)
    logger.info('\n*** Time taken for rethinkdb is [{}] ***\n'.format(
        (time.time() - start_rethinkdb_time) / 60))

    aggregator_thread.join()
    logger.info('\n*** Time taken for aggregator setup is [{}] ***\n'.format(
        (time.time() - start_aggregator_time) / 60))

    efs.setup_valor_keys()
    efs.setup_valor_router()

    standby_pools = StandbyPools(stack_name, sshkey)
    start_standby_valor_pools_time = time.time()
    standby_valor_pools_thread = threading.Thread(
        target=standby_pools.initialize_valor_standby_pool, name="valorpool")
    standby_valor_pools_thread.start()

    standby_valor_pools_thread.join()
    logger.info(
        '\n*** Time taken for Standby Pools of Valor is [{0}] ***\n'.format(
            (time.time() - start_standby_valor_pools_time) / 60))

    # Wait for creation of base ubuntu, unity and standby role image files
    threads_pending = True
    while threads_pending:
        threads_pending = False
        for thread in create_img_file_threads:
            threads_pending = True
            if not thread["thread"].is_alive():
                create_img_file_threads.remove(thread)
            else:
                time.sleep(10)

    # Done with XenPVMBuilder - shutdown the node
    efs.shutdown_xen_pvm_builder()

    if not deactivate_virtue_migration:
        migration = AutomatedVirtueMigration(stack_name, sshkey)
        migration.activate_automated_virtue_migration(auto_migration_interval)

    logger.info('\n*** Time taken for Setup is [{}] ***\n'.format(
        (time.time() - start_setup_time) / 60))

    logger.info(
        '*** Total Time taken for Galahad Deployment is [{}] ***\n'.format(
            (time.time() - start_stack_time) / 60))


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i",
        "--sshkey",
        type=str,
        required=True,
        help="The path to the SSH key used for the ec2 instances")
    parser.add_argument(
        "-n",
        "--stack_name",
        type=str,
        required=True,
        help="The name of the cloudformation stack for the virtue environment")
    parser.add_argument(
        "-s",
        "--stack_suffix",
        type=str,
        required=True,
        help="The suffix used by the cloudformation stack to append to resource names")
    parser.add_argument(
        "--import_stack",
        type=str,
        default='None',
        required=False,
        help="The Name of the Stack containing resources that will be imported for use in this stack")
    parser.add_argument(
        "-b",
        "--branch_name",
        type=str,
        default="master",
        help="The branch name to be used for excalibur repo")
    parser.add_argument(
        "--aws_config",
        type=str,
        required=False,
        default='setup/aws_config',
        help="AWS config to be used to communicate with AWS")
    parser.add_argument(
        "--aws_keys",
        type=str,
        required=True,
        help="AWS keys to be used for AWS communication")
    parser.add_argument(
        '--key_name',
        type=str,
        default='starlab-virtue-te',
        help='The key pair name to use, defaults to starlab-virtue-te.')

    parser.add_argument(
        "--setup",
        action="store_true",
        help="setup the galahad/virtue test environment")
    parser.add_argument(
        "--setup_stack",
        action="store_true",
        help="setup the galahad/virtue stack only")
    parser.add_argument(
        "--list_stacks",
        action="store_true",
        help="List all the available stacks")
    parser.add_argument(
        "--delete_stack",
        action="store_true",
        help="delete the specified stack")
    parser.add_argument(
        "--image_size",
        nargs="+",
        default=["8GB"],
        help="Indicate size of initial ubuntu image to be created (default: %(default)s)")
    parser.add_argument(
        "--build_image_only",
        action="store_true",
        help="Build the ubuntu and unity image only - Assume an existing stack")
    parser.add_argument(
        "-d",
        "--deactivate_virtue_migration",
        action="store_true",
        help="Deactivate automated migration of Virtues")
    parser.add_argument(
        "--auto_migration_interval",
        default=300,
        type=int,
        help="Specify the interval at which Virtues are automatically migrated")

    args = parser.parse_args()

    return args


def ensure_required_files_exist(args):
    required_files = '{} {} {}'.format(
        args.sshkey,
        args.aws_config,
        args.aws_keys)

    for file in required_files.split():

        if not os.path.isfile(file):
            logger.error('Specified file [{}] does not exit!\n'.format(file))
            sys.exit()


def main():
    args = parse_args()

    ensure_required_files_exist(args)

    if args.setup:
        setup(args.sshkey, args.stack_name, args.stack_suffix, args.import_stack,
              args.aws_config, args.aws_keys, args.branch_name, args.image_size,
              args.deactivate_virtue_migration, args.auto_migration_interval, args.key_name)

    if args.setup_stack:
        stack = Stack()
        stack.setup_stack(STACK_TEMPLATE, args.stack_name, args.stack_suffix,
                          args.key_name, args.import_stack)

    if args.list_stacks:
        Stack().list_stacks()

    if args.delete_stack:
        Stack().delete_stack(args.stack_name)

    if args.build_image_only:
        create_img_file_threads = []
        for image in args.image_size:
            create_img_file_start_time = time.time()
            create_img_file_thread = threading.Thread(
                target=create_and_setup_image_unity_files,
                args=(args.stack_name, args.sshkey, image,))
            create_img_file_thread.start()
            create_img_file_threads.append(
                {
                    "image_size": image,
                    "start_time": create_img_file_start_time,
                    "thread": create_img_file_thread
                })

        threads_pending = True
        while threads_pending:
            threads_pending = False
            for thread in create_img_file_threads:
                threads_pending = True
                if not thread["thread"].is_alive():
                    create_img_file_threads.remove(thread)
                else:
                    time.sleep(10)


if __name__ == '__main__':
    main()
