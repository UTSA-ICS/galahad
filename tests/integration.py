#!/usr/bin/python

import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if (__name__ == '__main__'):
    from common import ssh_tool
    import common


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
        '-e',
        '--excalibur_server_ip',
        type=str,
        required=False,
        help='The IP address of an existing aws excalibur instance.')
    parser.add_argument(
        '--test_sso', action='store_true', help='The ldap API Tests')
    parser.add_argument(
        '--test_admin_api', action='store_true', help='The ADMIN API Tests')
    parser.add_argument(
        '--test_user_api', action='store_true', help='The USER API Tests')
    parser.add_argument(
        '--run_all_tests',
        action='store_true',
        help='Run All available Integration Tests')

    arg = parser.parse_args()

    return arg


if (__name__ == '__main__'):

    args = parse_args()

    excalibur_ip = None
    if args.stack_name != None:
        excalibur_ip = common.get_excalibur_server_ip(args.stack_name)
    elif args.excalibur_server_ip != None:
        excalibur_ip = args.excalibur_server_ip
    else:
        logger.error(
            '\nPlease specify either stack_name or excalibur_user_ip!\n')
        sys.exit()

    logger.info(
        '\n!!!!!!!!!\nRunning Tests on excalibur server [{}]\n!!!!!!!!!!'.
        format(excalibur_ip))

    ssh_inst = ssh_tool('ubuntu', excalibur_ip, sshkey=args.sshkey)

    # Populate the excalibur_ip file needed for all the tests.
    ssh_inst.ssh('cd galahad/tests/setup && echo {} > excalibur_ip'.format(
        excalibur_ip))

    if args.test_sso:
        ssh_inst.ssh('cd galahad/tests/integration && pytest test_sso.py')
    if args.test_admin_api:
        ssh_inst.ssh(
            'cd galahad/tests/integration && pytest test_admin_api.py')
    if args.test_user_api:
        ssh_inst.ssh('cd galahad/tests/integration && pytest test_user_api.py')
    if args.run_all_tests:
        ssh_inst.ssh('cd galahad/tests/integration && pytest')