#!/usr/bin/python3

# Copyright (c) 2019 by Star Lab Corp.

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
import tarfile
from pprint import pformat

import boto3
import botocore
from sultan.api import Sultan, SSHConfig

# File names
STACK_TEMPLATE = 'setup/galahad-stack.yaml'
VPC_STACK_TEMPLATE = 'setup/galahad-vpc-stack.yaml'

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
        if 'deploy_galahad' in str(cmd):
            logger.info('\nstdout: {}\nstderr: {}\nsuccess: {}'.format(
                pformat(result.stdout),
                pformat(result.stderr),
                pformat(result.is_success)))

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

    def setup_stack(self, stack_template, stack_name, suffix_value, key_name):

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

    def checkout_repo(self, repo, branch='master'):
        # Cleanup any left over repos
        run_ssh_cmd(self.server_ip, self.ssh_key, "rm('-rf {}')".format(repo))
        #
        if branch == 'master':
            _cmd = "git('clone https://gitlab.com/utsa-ics/galahad/{}.git')".format(repo)
        else:
            _cmd = "git('clone https://gitlab.com/utsa-ics/galahad/{}.git -b {}')".format(
                repo, branch)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

    def copy_config(self, config_path):
        run_ssh_cmd(self.server_ip, self.ssh_key, "rm('-rf ~/galahad-config')")

        config_filename = config_path.split('/')[-1]
        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:{} '.
                format(self.ssh_key, config_path, self.server_ip, config_filename)).run()
        run_ssh_cmd(self.server_ip, self.ssh_key, "tar('-xf ~/{}')".format(config_filename))

    def setup_aws_access(self, aws_config, aws_keys):
        run_ssh_cmd(self.server_ip, self.ssh_key, "mkdir('-p ~/.aws')")
        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/.aws/config '.
                format(self.ssh_key, aws_config, self.server_ip)).run()
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {} ubuntu@{}:~/.aws/credentials '.
                format(self.ssh_key, aws_keys, self.server_ip)).run()

    def setup(self, branch, aws_config, aws_keys, stack_suffix, key_name, config_tarfile):

        logger.info(
            'Now checking out relevant galahad repos for {} branch'.format(
                branch))

        time.sleep(10)
        # Check out galahad repos required for galahad
        self.copy_config(config_tarfile)
        self.checkout_repo('galahad', branch)

        # Sleep for 10 seconds to ensure that both repos are completely checked out
        time.sleep(10)

        # Setup the config and keys for AWS communication
        self.setup_aws_access(aws_config, aws_keys)

        # Setup the Default key to be able to login to the install nodes
        GALAHAD_KEY_DIR = '~/user-keys'

        _cmd = "mkdir('-p {}')".format(GALAHAD_KEY_DIR)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {0} {0} ubuntu@{1}:{2}/{3}.pem'.
                format(self.ssh_key, self.server_ip, GALAHAD_KEY_DIR,
                       key_name)).run()

        _cmd = "sudo('chmod 600 {0}/{1}.pem')".format(GALAHAD_KEY_DIR, key_name)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

        # Deploy the Pre-requisites
        _cmd = "sudo('apt-get update')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

        _cmd = "sudo('apt-get install -y python-minimal python-pip python3-dev python3-pip')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

        _cmd = "sudo('pip3 install -r galahad/deploy/requirements.txt')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

        # Start the normal deployment process - Run the setup script
        _cmd = '''bash(('-c "cd galahad/deploy && python3 deploy_galahad.py'
                        ' -i {0}/{1}.pem'
                        ' --aws_config ~/.aws/config'
                        ' --aws_keys ~/.aws/credentials'
                        ' --key_name {1}'
                        ' -b {2}'
                        ' -s {3}'
                        ' -n {4}'
                        ' --deactivate_virtue_migration'
                        ' --import_stack {5}'
                        ' --setup"'))'''.format(GALAHAD_KEY_DIR, key_name, branch, stack_suffix, self.stack_name,
                                                self.import_stack_name)
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)


def setup(sshkey, stack_name, stack_suffix, aws_config, aws_keys, branch, key_name, config_tarfile):

    stack = VPC_Stack()
    stack.setup_stack(VPC_STACK_TEMPLATE, stack_name, stack_suffix, key_name)

    deploy = DeployServer(stack_name, sshkey)
    deploy.setup(branch, aws_config, aws_keys, stack_suffix, key_name, config_tarfile)


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
        '--key_name',
        type=str,
        default='starlab-virtue-te',
        help='The key pair name to use, defaults to starlab-virtue-te.')
    parser.add_argument(
        '--config_tarfile',
        type=str,
        required=True,
        help='The tarred galahad-config file to use for the deployment (with certs and keys for galahad components).')

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

    args = parser.parse_args()
    print(args)

    return args


def ensure_required_files_exist(args):
    required_files = '{} {} {}'.format(
        args.sshkey,
        args.aws_config,
        args.aws_keys,
        args.config_tarfile)

    for file in required_files.split():

        if not os.path.isfile(file):
            logger.error('Specified file [{}] does not exit!\n'.format(file))
            sys.exit()
        if file == args.config_tarfile:
            tarcontents = tarfile.TarFile(file, 'r')
            if tarcontents.getnames()[0] != 'galahad-config':
                logger.error('Specified config file tar, {}, does not have ',
                             'the correct directory name.\n'.format(tarcontents.getnames()[0]))
                logger.error('The correct name of the directory should be [galahad-config].\n')
                sys.exit()


def main():
    args = parse_args()

    ensure_required_files_exist(args)

    if args.setup:
        setup(args.sshkey, args.stack_name, args.stack_suffix, args.aws_config,
              args.aws_keys, args.branch_name, args.key_name, args.config_tarfile)

    if args.list_stacks:
        VPC_Stack().list_stacks()

    if args.delete_stack:
        VPC_Stack().delete_stack(args.stack_name)


if __name__ == '__main__':
    main()
