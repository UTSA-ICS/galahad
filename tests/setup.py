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

# File names
STACK_TEMPLATE = 'setup/virtue-ci-stack.yaml'
EXCALIBUR_IP = 'setup/excalibur_ip'
AWS_INSTANCE_INFO = 'setup/aws_instance_info.json'

# aws public key name used for the instances
key_name = 'starlab-virtue-te'

# Configure the Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Stack():
    def read_template(self):
        file = open(self.stack_template, "r")
        return file.read()

    def setup_stack(self, stack_template, stack_name, suffix_value):
        self.stack_template = stack_template
        self.stack_name = stack_name
        self.suffix_value = suffix_value
        #
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
                logger.info('{} {} {}'.format(event['Timestamp'],
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

    def list_stacks(self):
        client = boto3.client('cloudformation')
        response = client.list_stacks()
        for stack in response['StackSummaries']:
            if 'UPDATE' in stack['StackStatus'] or 'CREATE' in stack['StackStatus']:
                logger.info('{} {} {}'.format(stack['StackName'],
                                              stack['CreationTime'],
                                              stack['StackStatus']))


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
        # Return public IP
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

    def setup_excalibur(self, branch, github_key, aws_config, aws_keys, user_key):

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

        # Start the flask-server (excalibur)
        _cmd3 = "cd('galahad/excalibur').and_().bash('./start-screen.sh')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd3)

        # Setup the transducer heartbeat Listener and Start it
        _cmd4 = "cd('galahad/transducers').and_().bash('./install_heartbeatlistener.sh')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd4)

        # Setup the Default key to be able to login to the virtues.
        # This private key's corresponding public key will be used for the virtues
        GALAHAD_KEY_DIR = '~/galahad-keys'
        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {0} {0} ubuntu@{1}:{2}/default-virtue-key.pem'.
                format(self.ssh_key, self.server_ip, GALAHAD_KEY_DIR)).run()

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
        response1 = security_group.authorize_ingress(
            CidrIp='70.121.205.81/32',
            FromPort=22,
            ToPort=22,
            IpProtocol='TCP')
        response2 = security_group.authorize_ingress(
            CidrIp='172.3.30.184/32', FromPort=22, ToPort=22, IpProtocol='TCP')
        response3 = security_group.authorize_ingress(
            CidrIp='35.170.157.4/32', FromPort=22, ToPort=22, IpProtocol='TCP')
        response4 = security_group.authorize_ingress(
            CidrIp='129.115.2.249/32',
            FromPort=22,
            ToPort=22,
            IpProtocol='TCP')
        response5 = security_group.authorize_ingress(
            CidrIp='70.121.205.81/32',
            FromPort=5002,
            ToPort=5002,
            IpProtocol='TCP')
        response6 = security_group.authorize_ingress(
            CidrIp='172.3.30.184/32',
            FromPort=5002,
            ToPort=5002,
            IpProtocol='TCP')
        response7 = security_group.authorize_ingress(
            CidrIp='35.170.157.4/32',
            FromPort=5002,
            ToPort=5002,
            IpProtocol='TCP')
        response8 = security_group.authorize_ingress(
            CidrIp='129.115.2.249/32',
            FromPort=5002,
            ToPort=5002,
            IpProtocol='TCP')
        response9 = security_group.authorize_ingress(
            CidrIp='{}/32'.format(self.server_ip),
            FromPort=5002,
            ToPort=5002,
            IpProtocol='TCP')
        return dict(
            list(response1.items()) + list(response2.items()) +
            list(response3.items()) + list(response4.items()) +
            list(response5.items()) + list(response6.items()) +
            list(response7.items()) + list(response8.items()) +
            list(response9.items()))


def run_ssh_cmd(host_server, path_to_key, cmd):
    config = SSHConfig(
        identity_file=path_to_key, option='StrictHostKeyChecking=no')
    with Sultan.load(
            user='ubuntu', hostname=host_server, ssh_config=config) as s:
        result = eval('s.{}.run()'.format(cmd))
        logger.info('\nstdout: {}\nstderr: {}\nsuccess: {}'.format(
            result.stdout, result.stderr, result.is_success))
        assert result.rc == 0
        return result


def setup(path_to_key, stack_name, stack_suffix, github_key, aws_config,
          aws_keys, branch, user_key):
    stack = Stack()
    stack.setup_stack(STACK_TEMPLATE, stack_name, stack_suffix)

    excalibur = Excalibur(stack_name, path_to_key)
    excalibur.setup_excalibur(branch, github_key, aws_config, aws_keys, user_key)


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
        "The suffix used by the cloudformation stack to append to resource names"
    )
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
        "--setup_ldap",
        action="store_true",
        help="setup the ldap related test environment")
    parser.add_argument(
        "--update_excalibur",
        action="store_true",
        help="Update the excalibur server/code")
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


def main():
    args = parse_args()

    # Check if the required files exist
    required_files = '{} {} {} {}'.format(
        args.path_to_key, args.github_repo_key, args.aws_config, args.aws_keys)
    for file in required_files.split():
        if not os.path.isfile(file):
            logger.error('Specified file [{}] does not exit!\n'.format(file))
            sys.exit()

    if args.setup:
        setup(args.path_to_key, args.stack_name, args.stack_suffix,
              args.github_repo_key, args.aws_config, args.aws_keys,
              args.branch_name, args.default_user_key)
    if args.setup_ldap:
        excalibur = Excalibur(args.stack_name, args.path_to_key)
        excalibur.setup_ldap()
    if args.update_excalibur:
        logger.warn('Not yet implemented!')
    if args.list_stacks:
        Stack().list_stacks()
    if args.delete_stack:
        Stack().delete_stack(args.stack_name)


if __name__ == '__main__':
    main()
