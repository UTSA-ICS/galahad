#!/usr/bin/python3

###
# Test CI Orchestration:
# - Setup Stack and Virtue Environment
# - Start to collect system information to be able to run tests
# -  - Get IP for LDAP/AD
# - Checkout latest code
# -
###

import os
import sys
import boto3
import json
import time
import argparse
import logging
from sultan.api import Sultan, SSHConfig
from pprint import pformat

# File names
STACK_TEMPLATE = 'setup/virtue-ci-stack.yaml'
EXCALIBUR_IP = 'setup/excalibur_ip'
RETHINKDB_IP = 'setup/rethinkdb_ip'
AWS_INSTANCE_INFO = 'setup/aws_instance_info.json'

# aws public key name used for the instances
key_name = 'starlab-virtue-te'

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


    def setup_stack(self, stack_template, stack_name, suffix_value):

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
        cloudformation = boto3.resource('cloudformation')
        vpc_resource = cloudformation.StackResource(stack_name, 'VirtUEVPC')
        vpc_id = vpc_resource.physical_resource_id
        # Now find all instances in ec2 within the VPC but without the stack tags.
        ec2 = boto3.client('ec2')

        # Get ALL instances in the stack VPC
        instances_in_vpc = []
        vms = ec2.describe_instances(Filters=[ {'Name': 'vpc-id',
                                                'Values': [vpc_id]} ])
        for vm in vms['Reservations']:
            instances_in_vpc.append(vm['Instances'][0]['InstanceId'])

        # Get instances created by the stack
        instances_in_stack = []
        vms = ec2.describe_instances(Filters=[ {'Name': 'tag:aws:cloudformation:stack-name',
                                                'Values': [stack_name]} ])
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
        self.ip_address = self.get_ip_address()
        # Write out rethinkdb IP to a file
        self.write_ip_address(self.ip_address)


    def write_ip_address(self, ip_address):

        with open(RETHINKDB_IP, 'w') as f:
            f.write(ip_address)


    def get_ip_address(self):

        client = boto3.client('ec2')

        server = client.describe_instances(
            Filters=[{
                'Name': 'tag:aws:cloudformation:logical-id',
                'Values': ['RethinkDB']
            }, {
                'Name': 'tag:aws:cloudformation:stack-name',
                'Values': [self.stack_name]
            }, {
                'Name': 'instance-state-name',
                'Values': ['running']
            }])

        return server['Reservations'][0]['Instances'][0]['PublicIpAddress']


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
        self.server_ip = self.get_excalibur_server_ip()
        # Write out excalibur IP to a file
        self.write_excalibur_ip(self.server_ip)

    def write_excalibur_ip(self, excalibur_ip):

        with open(EXCALIBUR_IP, 'w') as f:
            f.write(excalibur_ip)

    def get_excalibur_server_ip(self):

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

        return server['Reservations'][0]['Instances'][0]['PublicIpAddress']


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
        self.update_security_rules()
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
        _cmd1 = "cd('galahad/tests/setup').and_().bash('./setup_excalibur.sh')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd1)

        # Call the setup_ldap.sh script for openldap installation and config.
        _cmd2 = "cd('galahad/tests/setup').and_().bash('./setup_ldap.sh')"
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
        _cmd7 = "cd('galahad/tests/setup').and_().bash('./setup_efs.sh {}')".format(efs.efs_id)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd7)

    def setup_aws_instance_info(self):
        client = boto3.client('cloudformation')
        subnet = client.describe_stack_resource(
            StackName=self.stack_name, LogicalResourceId='VirtUEAdminSubnet')
        subnet = subnet['StackResourceDetail']['PhysicalResourceId']
        aws_instance_info = {}
        aws_instance_info['image_id'] = 'ami-aa2ea6d0'
        aws_instance_info['inst_type'] = 't2.micro'
        aws_instance_info['subnet_id'] = subnet
        aws_instance_info['key_name'] = 'starlab-virtue-te'
        aws_instance_info['tag_key'] = 'Project'
        aws_instance_info['tag_value'] = 'Virtue'
        aws_instance_info['sec_group'] = self.get_default_security_group_id()
        aws_instance_info['inst_profile_name'] = ''
        aws_instance_info['inst_profile_arn'] = ''

        # Now write this to a file
        filename = AWS_INSTANCE_INFO.split('/')[-1]
        with open('/tmp/{0}'.format(filename), 'w') as f:
            json.dump(aws_instance_info, f)

        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {0} /tmp/{1} ubuntu@{2}:~/galahad/tests/{3}'.
                format(self.ssh_key, filename, self.server_ip, AWS_INSTANCE_INFO)).run()

        return aws_instance_info

    def get_vpc_id(self):
        ec2 = boto3.resource('ec2')
        vpc_filter = [{
            'Name': 'tag-key',
            'Values': ['aws:cloudformation:stack-name']
        }, {
            'Name': 'tag-value',
            'Values': [self.stack_name]
        }]
        vpc_id = list(ec2.vpcs.filter(Filters=vpc_filter))[0].id
        return vpc_id

    def get_default_security_group_id(self):
        client = boto3.client('ec2')
        vpc_id = self.get_vpc_id()
        group_filter = [{
            'Name': 'group-name',
            'Values': ['default']
        }, {
            'Name': 'vpc-id',
            'Values': [vpc_id]
        }]
        group_id = client.describe_security_groups(Filters=group_filter)
        return group_id['SecurityGroups'][0]['GroupId']

    def update_security_rules(self):
        group_id = self.get_default_security_group_id()
        ec2 = boto3.resource('ec2')
        security_group = ec2.SecurityGroup(group_id)
        client_cidrs_to_allow_access =  [ '{}/32'.format(self.server_ip),
                                          '70.121.205.81/32',
                                          '45.31.214.87/32',
                                          '35.170.157.4/32',
                                          '129.115.2.249/32',
                                          '199.46.124.36/32',
                                          '128.89.0.0/16' ]
        for cidr in client_cidrs_to_allow_access:
            security_group.authorize_ingress(
                CidrIp=cidr,
                FromPort=22,
                ToPort=22,
                IpProtocol='TCP')
            security_group.authorize_ingress(
                CidrIp=cidr,
                FromPort=5002,
                ToPort=5002,
                IpProtocol='TCP')


class EFS():
    def __init__(self, stack_name, ssh_key):
        self.stack_name = stack_name
        self.ssh_key = ssh_key
        self.efs_id = self.get_efs_id()
        self.nfs_ip = '18.210.83.5'

    def get_efs_id(self):
        cloudformation = boto3.resource('cloudformation')
        EFSStack = cloudformation.Stack(self.stack_name)

        for output in EFSStack.outputs:
            if output['OutputKey'] == 'FileSystemID':
                efs_id = output['OutputValue']

        efs_id = '{}.efs.us-east-1.amazonaws.com'.format(efs_id)
        logger.info('EFS File System ID is {}'.format(efs_id))

        return efs_id

    def setup_efs(self):
        client = boto3.client('ec2')
        efs = client.describe_instances(
            Filters=[{
                'Name': 'tag:aws:cloudformation:logical-id',
                'Values': ['ValorEFSServer']
            }, {
                'Name': 'tag:aws:cloudformation:stack-name',
                'Values': [self.stack_name]
            }, {
                'Name': 'instance-state-name',
                'Values': ['running']
            }])
        efs_ip = efs['Reservations'][0]['Instances'][0]['PublicIpAddress']

        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/.'.
                format(self.ssh_key, 'setup/setup_efs_server.sh', efs_ip)).run()

        # Call the setup_efs.sh script
        _cmd = "bash('./setup_efs_server.sh {} {}')".format(self.efs_id, self.nfs_ip)
        run_ssh_cmd(efs_ip, self.ssh_key, _cmd)

    def setup_valorNodes(self):

        self.configure_instance('ValorRouter', 'setup_valor_router.sh')
        self.configure_instance('ValorNode51', 'setup_valor_compute.sh')
        self.configure_instance('ValorNode52', 'setup_valor_compute.sh')

    def configure_instance(self, tag_logical_id, setup_filename):
        # Get the IP for the instances specified by the logical-id tag
        client = boto3.client('ec2')
        efs = client.describe_instances(
            Filters=[{
                'Name': 'tag:aws:cloudformation:logical-id',
                'Values': [tag_logical_id]
            }, {
                'Name': 'tag:aws:cloudformation:stack-name',
                'Values': [self.stack_name]
            }, {
                'Name': 'instance-state-name',
                'Values': ['running']
            }])
        public_ip = efs['Reservations'][0]['Instances'][0]['PublicIpAddress']
        logger.info('Public IP for instance with logical-id [{}] is [{}]'.format(tag_logical_id, public_ip))

        # SCP over the setup file to the instance
        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {} ../valor/{} ubuntu@{}:~/.'.
                format(self.ssh_key, setup_filename, public_ip)).run()

        # Execute the setup file on the instance
        _cmd = "bash('./{} {}')".format(setup_filename, self.efs_id)
        run_ssh_cmd(public_ip, self.ssh_key, _cmd)




def setup(path_to_key, stack_name, stack_suffix, github_key, aws_config,
          aws_keys, branch, user_key):

    stack = Stack()
    stack.setup_stack(STACK_TEMPLATE, stack_name, stack_suffix)

    excalibur = Excalibur(stack_name, path_to_key)
    excalibur.setup(branch, github_key, aws_config, aws_keys, user_key)

    rethinkdb = RethinkDB(stack_name, path_to_key)
    rethinkdb.setup(branch, github_key, aws_config, aws_keys, user_key)

    efs = EFS(stack_name, path_to_key)
    efs.setup_efs()
    efs.setup_valorNodes()


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
        "-b",
        "--branch_name",
        type=str,
        default="master",
        help="The branch name to be used for excalibur repo")
    parser.add_argument(
        "--aws_config",
        type=str,
        required=True,
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
        "--setup_valor",
        action="store_true",
        help="setup EFS and Valor migration ecosystem test environment")
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
              args.github_repo_key, args.aws_config, args.aws_keys,
              args.branch_name, args.default_user_key)

    if args.setup_stack:

        stack = Stack()
        stack.setup_stack(STACK_TEMPLATE, args.stack_name, args.stack_suffix)
        #
        excalibur = Excalibur(args.stack_name, args.path_to_key)
        excalibur.update_security_rules()

    if args.setup_valor:

        stack = Stack()
        stack.setup_stack(STACK_TEMPLATE, args.stack_name, args.stack_suffix)
        #
        excalibur = Excalibur(args.stack_name, args.path_to_key)
        excalibur.update_security_rules()
        #
        efs = EFS(args.stack_name, args.path_to_key)
        efs.setup_efs()
        efs.setup_valorNodes()

    if args.list_stacks:
        Stack().list_stacks()

    if args.delete_stack:
        Stack().delete_stack(args.stack_name)


if __name__ == '__main__':
    main()
