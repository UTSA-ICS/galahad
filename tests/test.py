#!/usr/bin/python

import argparse
import logging
import sys

import boto3

from ssh_tool import ssh_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-n',
        '--stack_name',
        type=str,
        required=False,
        help='The path to the private key to use ssh with')
    parser.add_argument(
        '-i',
        '--sshkey',
        type=str,
        required=True,
        help='The path to the private key to use ssh with')
    parser.add_argument(
        '-t',
        '--test_type',
        type=str,
        required=True,
        help='The type of Test to run - integration or unit')
    parser.add_argument(
        '-v',
        '--virtue_ip',
        type=str,
        required=False,
        help='The IP address of an existing aws Virtue instance.')
    parser.add_argument(
        '-d',
        '--virtue_id',
        type=str,
        required=False,
        help='The Virtue ID of an existing aws Virtue instance.')
    parser.add_argument(
        '--run_test',
        type=str,
        help='The Integration/Unit Test that will be run')
    parser.add_argument(
        '--list_tests',
        action='store_true',
        help='List All available Integration/Unit Tests')
    parser.add_argument(
        '--run_all_tests',
        action='store_true',
        help='Run All available Integration/Unit Tests')

    arg = parser.parse_args()

    return arg


def get_deploy_server_ip(stack_name):
    cloudformation = boto3.client('cloudformation')
    resources = cloudformation.list_stack_resources(StackName=stack_name + '-VPC')

    server_id = None
    for resource in resources['StackResourceSummaries']:
        if 'DeployServer' in str(resource) and resource['ResourceType'] == 'AWS::EC2::Instance':
            server_id = resource['PhysicalResourceId']
            break

    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(server_id)

    return instance.public_ip_address


if (__name__ == '__main__'):

    args = parse_args()

    virtue_ip = None
    virtue_id = None
    deploy_server_ip = None

    if args.stack_name != None:
        deploy_server_ip = get_deploy_server_ip(args.stack_name)
    else:
        logger.error(
            '\nPlease specify either stack_name!\n')
        sys.exit()

    if args.test_type == 'integration':
        if args.run_all_tests or args.run_test == 'test_security_api.py':
            if args.virtue_ip != None:
                virtue_ip = args.virtue_ip
            else:
                logger.warn(
                    '\nWarning: a new Virtue will be created\n')

            if args.virtue_id != None:
                virtue_id = args.virtue_id
            else:
                logger.warn(
                    '\nWarning: a new Virtue will be created\n')
    elif args.test_type == 'unit':
        pass
    else:
        logger.error(
            '\nERROR: Invalid Test type specified - Please specify "integration" or "unit"\n')
        sys.exit()

    ssh_inst = ssh_tool('ubuntu', deploy_server_ip, sshkey=args.sshkey)

    # Run the specified Test command
    try:
        if args.list_tests:
            ssh_inst.ssh(
                'cd galahad/tests && python {0}.py -i ~/galahad-keys/starlab-virtue-te.pem --list_tests'.format(
                    args.test_type))
        if args.run_test:
            ssh_inst.ssh(
                'cd galahad/tests && python {0}.py -i ~/galahad-keys/starlab-virtue-te.pem --run_test {1}'.format(
                    args.test_type, args.run_test))
        if args.run_all_tests:
            ssh_inst.ssh('cd galahad/tests && python {0}.py -i ~/galahad-keys/starlab-virtue-te.pem '
                         '--run_all_tests'.format(args.test_type))

    except:
        raise
    finally:
        ssh_inst.scp_from('.',
                          '/home/ubuntu/galahad/tests/{0}-test-report.xml'.format(args.test_type))
        ssh_inst.scp_from('.',
                          '/home/ubuntu/galahad/tests/{0}-test-report.html'.format(args.test_type))
