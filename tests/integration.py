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
        '-a',
        '--aggregator_server_ip',
        type=str,
        required=False,
        help='The IP address of an existing aws aggregator instance.')

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
        help='The Integration Test that will be run')

    parser.add_argument(
        '--list_tests',
        action='store_true',
        help='List All available Integration Tests')

    parser.add_argument(
        '--run_all_tests',
        action='store_true',
        help='Run All available Integration Tests')

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

    arg = parser.parse_args()

    return arg


if (__name__ == '__main__'):

    args = parse_args()

    excalibur_ip = None
    aggregator_ip = None
    virtue_ip = None
    virtue_id = None

    if args.stack_name != None:
        excalibur_ip = common.get_excalibur_server_ip(args.stack_name)
        aggregator_ip = common.get_aggregator_server_ip(args.stack_name)
    else:
        if args.excalibur_server_ip != None:
            excalibur_ip = args.excalibur_server_ip
        else:
            logger.error(
                '\nPlease specify either stack_name or excalibur_user_ip!\n')
            sys.exit()

        if args.run_all_tests or args.run_test == 'test_security_api.py':
            if args.aggregator_server_ip != None:
                aggregator_ip = args.aggregator_server_ip
            else:
                logger.error(
                    '\nPlease specify either stack_name or aggregator_server_ip!\n')
                sys.exit()

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

    ssh_inst = ssh_tool('ubuntu', excalibur_ip, sshkey=args.sshkey)

    # Populate the excalibur_ip file needed for all the tests.
    ssh_inst.ssh('cd galahad/tests/setup && echo {} > excalibur_ip'.format(
        excalibur_ip))
    if aggregator_ip is not None:
        ssh_inst.ssh('cd galahad/tests/setup && echo {} > aggregator_ip'.format(
            aggregator_ip))
    if virtue_ip is not None:
        ssh_inst.ssh('cd galahad/tests/setup && echo {} > virtue_ip'.format(
            virtue_ip))
    if virtue_id is not None:
        ssh_inst.ssh('cd galahad/tests/setup && echo {} > virtue_id'.format(
            virtue_id))

    # Run the specified Test command

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

            logger.info(
                '\n!!!!!!!!!\nListing of All Integration Tests\n!!!!!!!!!!')

            ssh_inst.ssh('cd galahad/tests/integration && pytest {} {} --setup-plan '
                         '--html=integration-test-report.html --self-contained-html '
                         '--junit-xml=integration-test-report.xml'.format(verbose_tag, profile_tag))
        if args.run_test:
            logger.info(
                '\n!!!!!!!!!\nRunning Tests on excalibur server [{}]\n!!!!!!!!!!'.
                    format(excalibur_ip))
            ssh_inst.ssh(
                'cd galahad/tests/integration && pytest {} {} --setup-show --html=integration-test-report.html '
                '--self-contained-html --junit-xml=integration-test-report.xml {0}'.format(verbose_tag, profile_tag, args.run_test))

        if args.run_all_tests:

            logger.info(
                '\n!!!!!!!!!\nRunning Tests on excalibur server [{}]\n!!!!!!!!!!'.
                    format(excalibur_ip))

            ssh_inst.ssh(
                'cd galahad/tests/integration && pytest {} {} --setup-show --html=integration-test-report.html '
                '--self-contained-html --junit-xml=integration-test-report.xml'.format(verbose_tag, profile_tag))

        ssh_inst.scp_from('.',
                          '/home/ubuntu/galahad/tests/integration/integration-test-report.xml')
        ssh_inst.scp_from('.',
                          '/home/ubuntu/galahad/tests/integration/integration-test-report.html')
    except Exception as error:

        print(error)

        ssh_inst.scp_from('.',
                          '/home/ubuntu/galahad/tests/integration/integration-test-report.xml')
        ssh_inst.scp_from('.',
                          '/home/ubuntu/galahad/tests/integration/integration-test-report.html')
        raise
