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
import logging
import os
import sys
import time
from pprint import pformat

import boto3
from sultan.api import Sultan, SSHConfig

# File names
STACK_TEMPLATE = 'setup/galahad-stack.yaml'
VPC_STACK_TEMPLATE = 'setup/galahad-vpc-stack.yaml'

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

        if 'deploy_galahad' in str(cmd):
            logger.info('\nstdout: {}\nstderr: {}\nsuccess: {}'.format(
                pformat(result.stdout),
                pformat(result.stderr),
                pformat(result.is_success)))

        assert result.rc == 0

        return result


class VPC_Stack():

    def read_template(self):

        file = open(self.stack_template, "r")

        return file.read()

    def setup_stack(self, stack_template, stack_name, suffix_value):

        self.stack_template = stack_template
        self.stack_name = stack_name + '-VPC'
        self.suffix_value = suffix_value

        client = boto3.client('cloudformation')
        stack = client.create_stack(
            StackName=self.stack_name,
            TemplateBody=self.read_template(),
            Parameters=[{
                'ParameterKey': 'FarSideKeyPair',
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

        client = boto3.client('cloudformation')

        # Delete the galahad stack specified
        #   terminate extra instances created by galahad - e.g valors
        self.terminate_non_stack_instances(stack_name)

        response = list()
        response1 = client.delete_stack(StackName=stack_name)
        waiter = boto3.client('cloudformation').get_waiter(
            'stack_delete_complete')
        waiter.wait(StackName=stack_name)
        response.append(response1)

        # Now delete the -VPC stack that was created with the deployment server
        # if the stack exists
        vpc_stack_name = stack_name + '-VPC'
        skip_vpc_stack = False
        try:
            response2 = client.delete_stack(StackName=vpc_stack_name)
            response.append(response2)
        except botocore.exceptions.ClientError:
            skip_vpc_stack = True
            pass
        if not skip_vpc_stack:
            waiter = boto3.client('cloudformation').get_waiter(
                'stack_delete_complete')
            waiter.wait(StackName=vpc_stack_name)

        return (response)

    def list_stacks(self):
        client = boto3.client('cloudformation')
        response = client.list_stacks()
        for stack in response['StackSummaries']:
            if 'UPDATE' in stack['StackStatus'] or 'CREATE' in stack['StackStatus']:
                logger.info('{} {} {}'.format(
                    stack['StackName'],
                    stack['CreationTime'],
                    stack['StackStatus']))

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


class DeployServer():

    def __init__(self, stack_name, ssh_key):

        self.stack_name = stack_name
        self.import_stack_name = stack_name + '-VPC'
        self.ssh_key = ssh_key
        self.server_id = None
        self.server_ip = None
        self.update_aws_info()

    def update_aws_info(self):

        cloudformation = boto3.client('cloudformation')
        resources = cloudformation.list_stack_resources(StackName=self.import_stack_name)

        for resource in resources['StackResourceSummaries']:
            if 'DeployServer' in str(resource) and resource['ResourceType'] == 'AWS::EC2::Instance':
                self.server_id = resource['PhysicalResourceId']
                break

        ec2 = boto3.resource('ec2')
        instance = ec2.Instance(self.server_id)

        self.server_ip = instance.public_ip_address

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
        run_ssh_cmd(self.server_ip, self.ssh_key, "mkdir('-p ~/.aws')")
        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/.aws/config '.
                    format(self.ssh_key, aws_config, self.server_ip)).run()
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/.aws/credentials '.
                    format(self.ssh_key, aws_keys, self.server_ip)).run()

    def setup(self, branch, github_key, aws_config, aws_keys, user_key, stack_suffix):

        logger.info('Setting up key for github access')
        # Transfer the private key to the server to enable
        # it to access github without being prompted for credentials
        self.setup_keys(github_key, user_key)
        logger.info(
            'Now checking out relevant galahad repos for {} branch'.format(
                branch))
        # Check out galahad repos required for galahad
        self.checkout_repo('galahad-config')
        self.checkout_repo('galahad', branch)

        # Sleep for 10 seconds to ensure that both repos are completely checked out
        time.sleep(10)

        # Setup the config and keys for AWS communication
        self.setup_aws_access(aws_config, aws_keys)

        # Setup the Default key to be able to login to the install nodes
        GALAHAD_KEY_DIR = '~/galahad-keys'

        _cmd = "mkdir('-p {}')".format(GALAHAD_KEY_DIR)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {0} {0} ubuntu@{1}:{2}/starlab-virtue-te.pem'.
                    format(self.ssh_key, self.server_ip, GALAHAD_KEY_DIR)).run()

        # Deploy the Pre-requisites
        _cmd = "sudo('apt update')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

        _cmd = "sudo('apt install -y python-minimal python-pip python3-dev python3-pip')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

        _cmd = "sudo('pip install boto3')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

        _cmd = "sudo('pip3 install boto3 sultan')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

        # Start the normal deployment process - Run the setup script
        _cmd = '''bash(('-c "cd galahad/deploy && python3 deploy_galahad.py'
                        ' -k {0}/{1}.pem'
                        ' -g ~/.ssh/id_rsa'
                        ' --aws_config ~/.aws/config'
                        ' --aws_keys ~/.aws/credentials'
                        ' --default_user_key {0}/{1}.pem'
                        ' -b {2}'
                        ' -s {3}' 
                        ' -n {4}'
                        ' --import_stack {5}'
                        ' --setup"'))'''.format(GALAHAD_KEY_DIR, key_name, branch, stack_suffix, self.stack_name,
                                                self.import_stack_name)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)


def setup(path_to_key, stack_name, stack_suffix, github_key, aws_config,
          aws_keys, branch, user_key):
    stack = VPC_Stack()
    stack.setup_stack(VPC_STACK_TEMPLATE, stack_name, stack_suffix)

    deploy = DeployServer(stack_name, path_to_key)
    deploy.setup(branch, github_key, aws_config, aws_keys, user_key, stack_suffix)


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
        help="The branch name to be used for galahad repo")
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
        setup(args.path_to_key, args.stack_name, args.stack_suffix, args.github_repo_key, args.aws_config,
              args.aws_keys, args.branch_name, args.default_user_key)

    if args.list_stacks:
        VPC_Stack().list_stacks()

    if args.delete_stack:
        VPC_Stack().delete_stack(args.stack_name)


if __name__ == '__main__':
    main()
