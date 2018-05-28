#!/usr/bin/python3

###
# Test CI Orchestration:
# - Setup Stack and Virtue Environment
# - Start to collect system information to be able to run tests
# -  - Get IP for LDAP/AD
# - Checkout latest code
# - Run SSO Test to get access Token
# - Run API Tests
# - Run Canvas Test - manually
# -
# -
# -
# -
# -
#
###

import boto3
import json
import time
import argparse
import logging
from sultan.api import Sultan, SSHConfig

stack_template = 'virtue-ci-stack.yaml'
key_name = 'starlab-virtue-te'
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
        stack = client.create_stack(StackName=self.stack_name,
                                    TemplateBody=self.read_template(),
                                    Parameters=[
                                        {'ParameterKey': 'KeyName',
                                         'ParameterValue': key_name},
                                        {'ParameterKey': 'NameSuffix',
                                         'ParameterValue': self.suffix_value}
                                        ])

        logger.info('Starting up Stack [{}] ...'.format(self.stack_name))
        waiter = client.get_waiter('stack_create_complete')
        waiter.wait(StackName=self.stack_name)

        # Log the events of the Stack
        response = client.describe_stack_events(StackName=self.stack_name)
        for event in response['StackEvents']:
            if 'CREATE_COMPLETE' in event['ResourceStatus']:
                logger.info(
                    '{} {} {}'.format(event['Timestamp'], event['ResourceType'],
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
        security_groups = client.describe_security_groups(Filters=[
            {'Name': 'tag-key',
             'Values': ['aws:cloudformation:stack-name']
             },
            {'Name': 'tag-value',
             'Values': [self.stack_name]
             }
            ]
            )
        ec2 = boto3.resource('ec2')
        for group in security_groups['SecurityGroups']:
            sec_group = ec2.SecurityGroup(group['GroupId'])
            if sec_group.ip_permissions:
                sec_group.revoke_ingress(IpPermissions=sec_group.ip_permissions)
            if sec_group.ip_permissions_egress:
                sec_group.revoke_egress(
                    IpPermissions=sec_group.ip_permissions_egress)

    def list_stacks(self):
        client = boto3.client('cloudformation')
        response = client.list_stacks()
        for stack in response['StackSummaries']:
            if 'UPDATE' in stack['StackStatus'] or 'CREATE' in stack[
                'StackStatus']:
                logger.info(
                    '{} {} {}'.format(stack['StackName'], stack['CreationTime'],
                                      stack['StackStatus']))


class Excalibur():

    def __init__(self, stack_name, ssh_key, github_key):
        self.stack_name = stack_name
        self.ssh_key = ssh_key
        self.github_key = github_key
        self.server_ip = self.get_excalibur_server_ip()

    def get_excalibur_server_ip(self):
        client = boto3.client('ec2')
        server = client.describe_instances(Filters=[
            {'Name': 'tag:aws:cloudformation:logical-id',
             'Values': ['ExcaliburServer']},
            {'Name': 'tag:aws:cloudformation:stack-name',
             'Values': [self.stack_name]},
            {'Name': 'instance-state-name', 'Values': ['running']}
            ])
        # Return public IP
        return server['Reservations'][0]['Instances'][0]['PublicIpAddress']

    def setup_keys(self):
        with Sultan.load() as s:
            s.scp(
                '-o StrictHostKeyChecking=no -i {} {}* ubuntu@{}:~/github_key '.format(
                    self.ssh_key, self.github_key,
                    self.server_ip)).run()

        _cmd1 = "mv('github_key ~/.ssh/id_rsa').and_().chmod('600 ~/.ssh/id_rsa')"
        result1 = run_ssh_cmd(self.server_ip, self.ssh_key, _cmd1)

        # Now remove any existing public keys as they will conflict with the private key
        result2 = run_ssh_cmd(self.server_ip, self.ssh_key,
                              "rm('-f ~/.ssh/id_rsa.pub')")

        result = list()
        result.append(result1.stdout)
        result.append(result2.stdout)
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

    def setup_excalibur(self, branch):

        logger.info('Setting up key for github access')
        self.update_security_rules()
        self.setup_keys()
        # Transfer the private key to the server to enable
        # it to access github without being prompted for credentials
        # Check out galahad repos required for excalibur
        logger.info(
            'Now checking out relevant excalibur repos for {} branch'.format(
                branch))
        self.checkout_repo('galahad-config')
        self.checkout_repo('galahad', branch)

        # Sleep for 10 seconds to ensure that both repos are completely checked out
        time.sleep(10)

        _cmd = "cd('galahad/flask-authlib').and_().bash('./start-screen.sh')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

    def setup_ldap(self):

        logger.info('Setup LDAP config for Tests')
        # Call setup_ldap on the server
        _cmd = "cd('galahad/tests').and_().bash('./setup_ldap.sh')"
        run_ssh_cmd(self.server_ip, self.ssh_key, _cmd)

    def get_vpc_id(self):
        ec2 = boto3.resource('ec2')
        vpc_filter = [
            {'Name': 'tag-key',
             'Values': ['aws:cloudformation:stack-name']
             },
            {'Name': 'tag-value',
             'Values': [self.stack_name]
             }
            ]
        vpc_id = list(ec2.vpcs.filter(Filters=vpc_filter))[0].id
        return vpc_id

    def get_default_security_group_id(self):
        client = boto3.client('ec2')
        vpc_id = self.get_vpc_id()
        group_filter = [
            {'Name': 'group-name',
             'Values': ['default']
             },
            {'Name': 'vpc-id',
             'Values': [vpc_id]
             }
            ]
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
            IpProtocol='TCP'
            )
        response2 = security_group.authorize_ingress(
            CidrIp='172.3.30.184/32',
            FromPort=22,
            ToPort=22,
            IpProtocol='TCP'
            )
        response3 = security_group.authorize_ingress(
            CidrIp='54.236.36.79/32',
            FromPort=22,
            ToPort=22,
            IpProtocol='TCP'
            )
        response4 = security_group.authorize_ingress(
            CidrIp='129.115.2.249/32',
            FromPort=22,
            ToPort=22,
            IpProtocol='TCP'
            )
        return dict(
            list(response1.items()) + list(response2.items()) +
            list(response3.items()) + list(response4.items()))


def run_ssh_cmd(host_server, path_to_key, cmd):
    config = SSHConfig(identity_file=path_to_key,
                       option='StrictHostKeyChecking=no')
    with Sultan.load(user='ubuntu', hostname=host_server,
                     ssh_config=config) as s:
        result = eval('s.{}.run()'.format(cmd))
        logger.debug(
            '\nstdout: {}\nstderr: {}\nsuccess: {}'.format(result.stdout,
                                                           result.stderr,
                                                           result.is_success))
        return result


def setup(path_to_key, stack_name, stack_suffix, github_key, branch):
    stack = Stack()
    stack.setup_stack(stack_template, stack_name, stack_suffix)

    excalibur = Excalibur(stack_name, path_to_key, github_key)
    excalibur.setup_excalibur(branch)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--path_to_key", type=str, required=True,
                        help="The path to the public key used for the ec2 instances")
    parser.add_argument("-g", "--github_repo_key", type=str, required=True,
                        help="The path to the key to be able to access github repos")
    parser.add_argument("-n", "--stack_name", type=str, required=True,
                        help="The name of the cloudformation stack for the virtue environment")
    parser.add_argument("-s", "--stack_suffix", type=str, required=True,
                        help="The suffix used by the cloudformation stack to append to resource names")
    parser.add_argument("-b", "--branch_name", type=str, default="master",
                        help="The branch name to be used for excalibur repo")
    parser.add_argument("--setup", action="store_true",
                        help="setup the galahad/virtue test environment")
    parser.add_argument("--setup_ldap", action="store_true",
                        help="setup the ldap related test environment")
    parser.add_argument("--update_excalibur", action="store_true",
                        help="Update the excalibur server/code")
    parser.add_argument("--list_stacks", action="store_true",
                        help="List all the available stacks")
    parser.add_argument("--delete_stack", action="store_true",
                        help="delete the specified stack")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    if args.setup:
        setup(args.path_to_key, args.stack_name, args.stack_suffix,
              args.github_repo_key, args.branch_name)
    if args.setup_ldap:
        excalibur = Excalibur(args.stack_name, args.path_to_key,
                              args.github_repo_key)
        excalibur.setup_ldap()
    if args.update_excalibur:
        logger.warn('Not yet implemented!')
    if args.list_stacks:
        Stack().list_stacks()
    if args.delete_stack:
        Stack().delete_stack(args.stack_name)


if __name__ == '__main__':
    main()
