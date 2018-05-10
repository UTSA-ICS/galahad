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
from sultan.api import Sultan, SSHConfig

stack_template = 'virtue-ci-stack.yaml'
key_name = 'starlab-virtue-te'


def read_template():
    file = open(stack_template, "r")
    return file.read()


def setup_stack(stack_name, suffix_value):
    client = boto3.client('cloudformation')
    stack = client.create_stack(StackName=stack_name,
                                TemplateBody=read_template(),
                                Parameters=[
                                    {'ParameterKey': 'KeyName',
                                     'ParameterValue': key_name
                                     },
                                    {'ParameterKey': 'NameSuffix',
                                     'ParameterValue': suffix_value
                                     }
                                ]
                                )
    return stack


def delete_stack(stack_name):
    client = boto3.client('cloudformation')
    clear_security_groups(stack_name)
    response = client.delete_stack(StackName=stack_name)
    waiter = boto3.client('cloudformation').get_waiter(
        'stack_delete_complete')
    waiter.wait(StackName=stack_name)
    return response


def clear_security_groups(stack_name):
    client = boto3.client('ec2')
    security_groups = client.describe_security_groups(Filters=[
        {'Name': 'tag-key',
         'Values': ['aws:cloudformation:stack-name']
         },
        {'Name': 'tag-value',
         'Values': [stack_name]
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


def get_vpc_id(stack_name):
    ec2 = boto3.resource('ec2')
    vpc_filter = [
        {'Name': 'tag-key',
         'Values': ['aws:cloudformation:stack-name']
         },
        {'Name': 'tag-value',
         'Values': [stack_name]
         }
    ]
    vpc_id = list(ec2.vpcs.filter(Filters=vpc_filter))[0].id
    return vpc_id


def get_default_security_group_id(stack_name):
    client = boto3.client('ec2')
    vpc_id = get_vpc_id(stack_name)
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


def add_local_security_rules(stack_name):
    group_id = get_default_security_group_id(stack_name)
    ec2 = boto3.resource('ec2')
    security_group = ec2.SecurityGroup(group_id)
    response = security_group.authorize_ingress(
        CidrIp='70.121.205.81/32',
        FromPort=22,
        ToPort=22,
        IpProtocol='TCP'
    )
    response = security_group.authorize_ingress(
        CidrIp='172.3.30.184/32',
        FromPort=22,
        ToPort=22,
        IpProtocol='TCP'
    )
    response = security_group.authorize_ingress(
        CidrIp='129.115.2.249/32',
        FromPort=22,
        ToPort=22,
        IpProtocol='TCP'
    )
    return response


def run_ssh_cmd(host_server, path_to_key, cmd):
    config = SSHConfig(identity_file=path_to_key,
                       option='StrictHostKeyChecking=no')
    with Sultan.load(user='ubuntu', hostname=host_server,
                     ssh_config=config) as s:
        # result = s.pwd().run()
        result = eval('s.{}.run()'.format(cmd))
        return result


def setup_server(host_server, path_to_key, github_key):
    # Transfer the private key to the server to enable
    # it to access github without being prompted for credentials
    with Sultan.load() as s:
        s.scp(
            '-o StrictHostKeyChecking=no -i {} {}* ubuntu@{}:~/github_key '.format(
                path_to_key, github_key,
                host_server)).run()
    _cmd1 = "mv('github_key ~/.ssh/id_rsa').and_().chmod('600 ~/.ssh/id_rsa')"
    result1 = run_ssh_cmd(host_server, path_to_key, _cmd1)
    # _cmd2 = "mv('github_key.public ~/.ssh/id_rsa.pub')"
    # result2 = run_ssh_cmd(host_server, path_to_key, _cmd2)
    return result1


def checkout_repo(host_server, path_to_key, repo):
    _cmd = "git('clone git@github.com:starlab-io/{}.git {}')".format(repo,
                                                                     repo)
    return run_ssh_cmd(host_server, path_to_key, _cmd)


def get_excalibur_server_ip(stack_name):
    client = boto3.client('ec2')
    server = client.describe_instances(Filters=[
        {'Name': 'tag:aws:cloudformation:logical-id',
         'Values': ['ExcaliburServer']},
        {'Name': 'tag:aws:cloudformation:stack-name', 'Values': [stack_name]}])
    # Return public IP
    return server['Reservations'][0]['Instances'][0]['PublicIpAddress']


def setup_env(path_to_key, stack_name, stack_suffix, github_key):
    setup_stack(stack_name, stack_suffix)
    waiter = boto3.client('cloudformation').get_waiter(
        'stack_create_complete')
    waiter.wait(StackName=stack_name)
    add_local_security_rules(stack_name)
    host_server = get_excalibur_server_ip(stack_name)
    setup_server(host_server, path_to_key, github_key)


def start_excalibur(stack_name, path_to_key):
    host_server = get_excalibur_server_ip(stack_name)
    checkout_repo(host_server, path_to_key, 'galahad-config')
    checkout_repo(host_server, path_to_key, 'galahad')

    print
    'sleeping for 10 seconds......pls wait......'
    time.sleep(10)

    _cmd = "cd('galahad/flask-authlib').and_().bash('./start-screen.sh')"
    return run_ssh_cmd(host_server, path_to_key, _cmd)


def parse_args():
    if __name__ == '__main__':
        parser = argparse.ArgumentParser()
        parser.add_argument("-k", "--path_to_key", type=str, required=True,
                            help="The path to the public key used for the ec2 instances")
        parser.add_argument("-g", "--github_repo_key", type=str, required=True,
                            help="The path to the key to be able to access github repos")
        parser.add_argument("-n", "--stack_name", type=str, required=True,
                            help="The name of the cloudformation stack for the virtue environment")
        parser.add_argument("-s", "--stack_suffix", type=str, required=True,
                            help="The suffix used by the cloudformation stack to append to resource names")
        parser.add_argument("--setup_env", action="store_true",
                            help="setup the galahad/virtue test environment")
        parser.add_argument("--start_excalibur", action="store_true",
                            help="start the excalibur server")
        parser.add_argument("--start_all", action="store_true",
                            help="setup and start the appropriate servers")
        parser.add_argument("--delete_stack", action="store_true",
                            help="delete the specified stack")
        args = parser.parse_args()
        return args


if __name__ == '__main__':
    args = parse_args()
    if args.setup_env:
        setup_env(args.path_to_key, args.stack_name, args.stack_suffix,
                  args.github_repo_key)
    if args.start_excalibur:
        start_excalibur(args.stack_name, args.path_to_key)
    if args.start_all:
        setup_env(args.path_to_key, args.stack_name, args.stack_suffix)
        start_excalibur(args.stack_name, args.path_to_key)
    if args.delete_stack:
        delete_stack(args.stack_name)
