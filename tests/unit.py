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
        '--run_test',
        type=str,
        help='The Unit Test that will be run')

    parser.add_argument(
        '--profile',
        action='store_true',
        required=False,
        help='enable profiling')

    parser.add_argument(
        '--verbose',
        action='store_true',
        required=False,
        help='enable verbose reporting')

    parser.add_argument(
        '--test_admin_api', action='store_true', help='The ADMIN API Tests')

    parser.add_argument(
        '--test_user_api', action='store_true', help='The USER API Tests')

    parser.add_argument(
        '--test_aws', action='store_true', help='The AWS Tests')

    parser.add_argument(
        '--list_tests',
        action='store_true',
        help='List All available Unit Tests')

    parser.add_argument(
        '--run_all_tests',
        action='store_true',
        help='Run All available unit Tests')

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

    ssh_inst = ssh_tool('ubuntu', excalibur_ip, sshkey=args.sshkey)

    # Now Run the specified Test command

    if args.verbose:
        verbose_tag = '--verbose'
    else:
        verbose_tag = ''

    if args.profile:
        profile_tag = '--profile'
    else:
        profile_tag = ''

    try:

        if args.list_tests:


            logger.info('\n!!!!!!!!!\nList All Unit Tests\n!!!!!!!!!!')

            ssh_inst.ssh('cd galahad/tests/unit && pytest --setup-plan {} {}'
                         '--html=integration-test-report.html --self-contained-html ' 
                         '--junit-xml=integration-test-report.xml'.format(verbose_tag, profile_tag))

        if args.run_test:

            logger.info(
                '\n!!!!!!!!!\nRun Test on excalibur server [{}]\n!!!!!!!!!!'.
                    format(excalibur_ip))

            ssh_inst.ssh('cd galahad/tests/unit && pytest --setup-show  {} {} --html=unit-test-report.html '
                         '--self-contained-html --junit-xml=unit-test-report.xml {}'.format(verbose_tag, profile_tag, args.run_test))

        if args.run_all_tests:

            ssh_inst.ssh('cd galahad/tests/unit && pytest {} {}  --setup-show --html=unit-test-report.html '
                         '--self-contained-html --junit-xml=unit-test-report.xml'.format(verbose_tag, profile_tag))

        ssh_inst.scp_from('.',
                          '/home/ubuntu/galahad/tests/unit/unit-test-report.xml')
        ssh_inst.scp_from('.',
                          '/home/ubuntu/galahad/tests/unit/unit-test-report.html')
    except:
        ssh_inst.scp_from('.',
                          '/home/ubuntu/galahad/tests/unit/unit-test-report.xml')
        ssh_inst.scp_from('.',
                          '/home/ubuntu/galahad/tests/unit/unit-test-report.html')
        raise
