#!/usr/bin/python3

###
# Test CI Orchestration:
# - Setup Stack and Virtue Environment
# - Start to collect system information to be able to run tests
# -  - Get IP for LDAP/AD
# - Checkout latest code
# -
###

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

# aws public key name used for the instances
key_name = 'starlab-virtue-te'

# Node addresses
EXCALIBUR_HOSTNAME = 'excalibur.galahad.com'
RETHINKDB_IP = 'rethinkdb.galahad.com'
VALOR_ROUTER_IP = 'valor-router.galahad.com'
XEN_PVM_BUILDER_IP = 'xenpvmbuilder.galahad.com'

# Configure the Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_ssh_cmd(host_server, path_to_key, cmd):
    config = SSHConfig(
        identity_file=path_to_key,
        option='StrictHostKeyChecking=no')

    with Sultan.load(
            user='ubuntu',
            hostname=host_server,
            ssh_config=config) as s:

        result = eval('s.{}.run()'.format(cmd))

        if result.is_success:
            logger.info('success: {}'.format(result.is_success))

        else:
            logger.info('\nstdout: {}\nstderr: {}\nsuccess: {}'.format(
                pformat(result.stdout),
                pformat(result.stderr),
                pformat(result.is_success)))

        assert result.rc == 0

        return result


class Stack():

    def read_template(self):

        file = open(self.stack_template, "r")

        return file.read()

    def setup_stack(self, stack_template, stack_name, suffix_value, import_stack_name='None'):

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
                'ParameterKey': 'EnvType',
                'ParameterValue': 'JHUAPL'
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
        excalibur = Excalibur(stack_name, None)
        vpc_id = excalibur.vpc_id

        # Now find all instances in ec2 within the VPC but without the stack tags.
        ec2 = boto3.client('ec2')

        # Get ALL instances in the stack VPC
        instances_in_vpc = []
        vms = ec2.describe_instances(Filters=[{'Name': 'vpc-id',
                                               'Values': [vpc_id]}])
        for vm in vms['Reservations']:
            instances_in_vpc.append(vm['Instances'][0]['InstanceId'])

        # Get instances created by the stack
        instances_in_stack = []
        vms = ec2.describe_instances(Filters=[{'Name': 'tag:aws:cloudformation:stack-name',
                                               'Values': [stack_name]}])
        for vm in vms['Reservations']:
            instances_in_stack.append(vm['Instances'][0]['InstanceId'])

        # Figure out which instances are not created by the stack
        instances_not_in_stack = []
        for instance in instances_in_vpc:
            if instance not in instances_in_stack:
                instances_not_in_stack.append(instance)

        # Now Terminate these instances not created by the stack
        resource = boto3.resource('ec2')
        for instance in instances_not_in_stack:
            resource.Instance(instance).terminate()
            print(instance)

    def list_stacks(self):
        client = boto3.client('cloudformation')
        response = client.list_stacks()
        for stack in response['StackSummaries']:
            if 'UPDATE' in stack['StackStatus'] or 'CREATE' in stack['StackStatus']:
                logger.info('{} {} {}'.format(
                    stack['StackName'],
                    stack['CreationTime'],
                    stack['StackStatus']))


class RethinkDB():

    def __init__(self, stack_name, ssh_key):

        self.stack_name = stack_name
        self.ssh_key = ssh_key
        self.ip_address = RETHINKDB_IP

    def setup_keys(self, github_key, user_key):

        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/github_key '.
                    format(self.ssh_key, github_key, self.ip_address)).run()
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/default-user-key.pem '.
                    format(self.ssh_key, user_key, self.ip_address)).run()

        _cmd1 = "mv('github_key ~/.ssh/id_rsa').and_().chmod('600 ~/.ssh/id_rsa')"
        result1 = run_ssh_cmd(self.ip_address, self.ssh_key, _cmd1)

        # Now remove any existing public keys as they will conflict with the private key
        result2 = run_ssh_cmd(self.ip_address, self.ssh_key,
                              "rm('-f ~/.ssh/id_rsa.pub')")

        # Now add the github public key to avoid host key verification prompt
        result3 = run_ssh_cmd(
            self.ip_address, self.ssh_key,
            "ssh__keyscan('github.com >> ~/.ssh/known_hosts')")

        result = list()
        result.append(result1.stdout)
        result.append(result2.stdout)
        result.append(result3.stdout)

        return (result)

    def checkout_repo(self, repo, branch='master'):
        # Cleanup any left over repos
        run_ssh_cmd(self.ip_address, self.ssh_key, "rm('-rf {}')".format(repo))

        if branch == 'master':
            _cmd = "git('clone git@github.com:starlab-io/{}.git')".format(repo)

        else:
            _cmd = "git('clone git@github.com:starlab-io/{}.git -b {}')".format(
                repo, branch)

        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd)

    def setup(self, branch, github_key, aws_config, aws_keys, user_key):

        # Transfer the private key to the server to enable
        # it to access github without being prompted for credentials
        self.setup_keys(github_key, user_key)

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
        self.checkout_repo('galahad-config')

        _cmd1 = "bash('./setup_rethinkdb.sh')"

        run_ssh_cmd(self.ip_address, self.ssh_key, _cmd1)


class Excalibur():

    def __init__(self, stack_name, ssh_key):

        self.stack_name = stack_name
        self.ssh_key = ssh_key
        self.server_ip = EXCALIBUR_HOSTNAME
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

    def setup_keys(self, github_key, user_key):

        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/github_key '.
                    format(self.ssh_key, github_key, self.server_ip)).run()
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/default-user-key.pem '.
                    format(self.ssh_key, user_key, self.server_ip)).run()

        _cmd1 = "mv('github_key ~/.ssh/id_rsa').and_().chmod('600 ~/.ssh/id_rsa')"
        result1 = run_ssh_cmd(self.server_ip, self.ssh_key, _cmd1)

        # Now remove any existing public keys as they will conflict with the private key
        result2 = run_ssh_cmd(self.server_ip, self.ssh_key,
                              "rm('-f ~/.ssh/id_rsa.pub')")

        # Now add the github public key to avoid host key verification prompt
        result3 = run_ssh_cmd(
            self.server_ip, self.ssh_key,
            "ssh__keyscan('github.com >> ~/.ssh/known_hosts')")

        result = list()
        result.append(result1.stdout)
        result.append(result2.stdout)
        result.append(result3.stdout)

        return (result)

    def checkout_repo(self, repo, branch='master'):
        # Cleanup any left over repos
        run_ssh_cmd(self.server_ip, self.ssh_key, "rm('-rf {}')".format(repo))
        #
        if branch == 'master':
            _cmd = "git('clone git@github.com:starlab-io/{}.git')".format(repo)
        else:
            _cmd = "git('clone git@github.com:starlab-io/{}.git -b {}')".format(
                repo, branch)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

    def setup_aws_access(self, aws_config, aws_keys):
        run_ssh_cmd(self.server_ip, self.ssh_key, "mkdir('~/.aws')")
        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/.aws/config '.
                    format(self.ssh_key, aws_config, self.server_ip)).run()
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/.aws/credentials '.
                    format(self.ssh_key, aws_keys, self.server_ip)).run()

    def setup(self, branch, github_key, aws_config, aws_keys, user_key):

        logger.info('Setting up key for github access')
        # Transfer the private key to the server to enable
        # it to access github without being prompted for credentials
        self.setup_keys(github_key, user_key)
        logger.info(
            'Now checking out relevant excalibur repos for {} branch'.format(
                branch))
        # Check out galahad repos required for excalibur
        self.checkout_repo('galahad-config')
        self.checkout_repo('galahad', branch)

        # Sleep for 10 seconds to ensure that both repos are completely checked out
        time.sleep(10)

        # Setup the config and keys for AWS communication
        self.setup_aws_access(aws_config, aws_keys)

        # Update /etc/hosts to resolve DNS records not using service discovery
        _cmd = "sudo('su - root -c \"echo 172.30.1.45 rethinkdb.galahad.com >> /etc/hosts\"')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)
        _cmd = "sudo('su - root -c \"echo 172.30.1.46 elasticsearch.galahad.com >> /etc/hosts\"')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

        # Call the setup_excalibur.sh script for system and pip packages.
        _cmd1 = "cd('galahad/deploy/setup').and_().bash('./setup_excalibur.sh')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd1)

        # Call the setup_ldap.sh script for openldap installation and config.
        _cmd2 = "cd('galahad/deploy/setup').and_().bash('./setup_ldap.sh')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd2)

        self.setup_aws_instance_info()

        # Setup the transducer heartbeat Listener and Start it
        _cmd3 = "cd('galahad/transducers').and_().bash('./install_heartbeatlistener.sh')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd3)

        # Start the flask-server (excalibur)
        _cmd4 = "cd('galahad/excalibur').and_().bash('./start-screen.sh')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd4)

        # Wait a min to Ensure that Excalibur setup is complete
        time.sleep(60)

        # Setup the Default key to be able to login to the virtues
        # This private key's corresponding public key will be used for the virtues
        GALAHAD_KEY_DIR = '~/galahad-keys'
        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {0} {0} ubuntu@{1}:{2}/default-virtue-key.pem'.
                    format(self.ssh_key, self.server_ip, GALAHAD_KEY_DIR)).run()

        # Copy over various other keys required for virtues
        GALAHAD_CONFIG_DIR = '~/galahad-config'
        _cmd5 = "cp('{0}/excalibur_pub.pem {1}/excalibur_pub.pem')".format(GALAHAD_CONFIG_DIR, GALAHAD_KEY_DIR)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd5)
        _cmd5 = "cp('{0}/rethinkdb_keys/rethinkdb_cert.pem {1}/')".format(GALAHAD_CONFIG_DIR, GALAHAD_KEY_DIR)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd5)

        # Now populate the /var/private/ssl dir for excalibur
        EXCALIBUR_PRIVATE_DIR = '/var/private/ssl'
        _cmd6 = "sudo('mkdir -p {0}').and_().sudo('chown -R ubuntu.ubuntu /var/private')".format(EXCALIBUR_PRIVATE_DIR)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd6)
        _cmd6 = "cp('{0}/excalibur_private_key.pem {1}/')".format(GALAHAD_CONFIG_DIR, EXCALIBUR_PRIVATE_DIR)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd6)
        _cmd6 = "cp('{0}/rethinkdb_keys/rethinkdb_cert.pem {1}/')".format(GALAHAD_CONFIG_DIR, EXCALIBUR_PRIVATE_DIR)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd6)
        _cmd6 = "cp('-r {0}/elasticsearch_keys {1}/')".format(GALAHAD_CONFIG_DIR, EXCALIBUR_PRIVATE_DIR)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd6)

        # Initialize the EFS class
        efs = EFS(self.stack_name, self.ssh_key)
        # Setup the EFS mount and populate Valor config files
        _cmd7 = "cd('galahad/deploy/setup').and_().bash('./setup_efs.sh {}')".format(efs.efs_id)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd7)

    def setup_aws_instance_info(self):
        aws_instance_info = {}
        aws_instance_info['image_id'] = 'ami-aa2ea6d0'
        aws_instance_info['inst_type'] = 't2.micro'
        aws_instance_info['subnet_id'] = self.subnet_id
        aws_instance_info['key_name'] = 'starlab-virtue-te'
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
                    format(self.ssh_key, filename, self.server_ip, AWS_INSTANCE_INFO)).run()

        return aws_instance_info


class EFS():

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
                    format(self.ssh_key, 'setup_valor_router.sh', VALOR_ROUTER_IP)).run()

        # Execute the setup file on the instance
        _cmd = "bash('./{} {}')".format('setup_valor_router.sh', self.efs_id)
        run_ssh_cmd(VALOR_ROUTER_IP, self.ssh_key, _cmd)

    def setup_ubuntu_img(self):

        # scp workaround payload to node
        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {} setup/xm.tmpl ubuntu@{}:~/.'.
                    format(self.ssh_key, XEN_PVM_BUILDER_IP)).run()
            s.scp(
                ('-o StrictHostKeyChecking=no -i {} '
                 'setup/sources.list ubuntu@{}:~/.').
                    format(self.ssh_key, XEN_PVM_BUILDER_IP)).run()
            s.scp(
                ('-o StrictHostKeyChecking=no -i {} '
                 'setup/setup_base_ubuntu_pvm.sh ubuntu@{}:~/.').
                    format(self.ssh_key, XEN_PVM_BUILDER_IP)).run()

        # Apply workarounds and create the ubuntu image
        ssh_cmd = "bash('setup_base_ubuntu_pvm.sh {0}')".format(self.efs_id)
        run_ssh_cmd(XEN_PVM_BUILDER_IP, self.ssh_key, ssh_cmd)

        # Delete xen tool instance
        # client.terminate_instances(InstanceIds=[instance['InstanceId']])

    def setup_unity_img(self, constructor_ip):

        pub_key = subprocess.run(['ssh-keygen', '-y', '-f', self.ssh_key],
                                 stdout=subprocess.PIPE).stdout

        pub_key_cmd = '''bash('-c "echo {0} > /tmp/unity_key.pub"')'''.format(
            pub_key.decode().strip())
        run_ssh_cmd(constructor_ip, self.ssh_key, pub_key_cmd)

        # Construct 8GB Unity
        construct_cmd = '''sudo(('python galahad/excalibur/call_constructor.py'
                                 ' -b /mnt/efs/images/base_ubuntu/8GB.img'
                                 ' -p /tmp/unity_key.pub'
                                 ' -o /mnt/efs/images/unities/8GB.img'
                                 ' -w /mnt/efs/tmp'))'''
        run_ssh_cmd(constructor_ip, self.ssh_key, construct_cmd)

        # Construct 4GB Unity
        construct_cmd = '''sudo(('python galahad/excalibur/call_constructor.py'
                                 ' -b /mnt/efs/images/base_ubuntu/4GB.img'
                                 ' -p /tmp/unity_key.pub'
                                 ' -o /mnt/efs/images/unities/4GB.img'
                                 ' -w /mnt/efs/tmp'))'''
        run_ssh_cmd(constructor_ip, self.ssh_key, construct_cmd)

        rm_cmd = "sudo('rm -rf /mnt/efs/images/domains')"
        run_ssh_cmd(constructor_ip, self.ssh_key, rm_cmd)


def setup(path_to_key, stack_name, stack_suffix, import_stack_name, github_key, aws_config,
          aws_keys, branch, user_key):
    stack = Stack()
    stack.setup_stack(STACK_TEMPLATE, stack_name, stack_suffix, import_stack_name)

    efs = EFS(stack_name, path_to_key)
    setup_ubuntu_img_thread = threading.Thread(target=efs.setup_ubuntu_img)
    setup_ubuntu_img_thread.start()

    excalibur = Excalibur(stack_name, path_to_key)
    excalibur.setup(branch, github_key, aws_config, aws_keys, user_key)

    rethinkdb = RethinkDB(stack_name, path_to_key)
    rethinkdb.setup(branch, github_key, aws_config, aws_keys, user_key)

    valor_node_thread = threading.Thread(target=efs.setup_valor_router)
    valor_node_thread.start()

    setup_ubuntu_img_thread.join()
    efs.setup_unity_img(excalibur.server_ip)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-k",
        "--path_to_key",
        type=str,
        required=True,
        help="The path to the public key used for the ec2 instances")
    parser.add_argument(
        "-g",
        "--github_repo_key",
        type=str,
        required=True,
        help="The path to the key to be able to access github repos")
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
        help=
        "The suffix used by the cloudformation stack to append to resource names")
    parser.add_argument(
        "--import_stack",
        type=str,
        default='None',
        required=False,
        help=
        "The Name of the Stack containing resources that will be imported for use in this stack")
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

    # Temporary:
    parser.add_argument(
        "--default_user_key",
        type=str,
        required=True,
        help="Default private key for users to get (Will be replaced with generated keys)")

    args = parser.parse_args()

    return args


def ensure_required_files_exist(args):
    required_files = '{} {} {} {}'.format(
        args.path_to_key,
        args.github_repo_key,
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
        setup(args.path_to_key, args.stack_name, args.stack_suffix,
              args.import_stack, args.github_repo_key, args.aws_config,
              args.aws_keys, args.branch_name, args.default_user_key)

    if args.setup_stack:
        stack = Stack()
        stack.setup_stack(STACK_TEMPLATE, args.stack_name, args.stack_suffix, args.import_stack)

    if args.list_stacks:
        Stack().list_stacks()

    if args.delete_stack:
        Stack().delete_stack(args.stack_name)


if __name__ == '__main__':
    main()
