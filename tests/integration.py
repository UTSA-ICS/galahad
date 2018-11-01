#!/usr/bin/python

import argparse
import logging

from ssh_tool import ssh_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXCALIBUR_HOSTNAME = 'excalibur.galahad.com'

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-i',
        '--sshkey',
        type=str,
        required=True,
        help='The path to the private key to use ssh with')

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
        help='The specified Integration Test that will be run')

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

    virtue_ip = None
    virtue_id = None

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

    ssh_inst = ssh_tool('ubuntu', EXCALIBUR_HOSTNAME, sshkey=args.sshkey)

    # Populate the virtue_ip and virtue_id file needed for all the tests.
    if virtue_ip is not None:
        ssh_inst.ssh('cd galahad/tests/integration && echo {} > virtue_ip'.format(
            virtue_ip))
    if virtue_id is not None:
        ssh_inst.ssh('cd galahad/tests/integration && echo {} > virtue_id'.format(
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
                    format(EXCALIBUR_HOSTNAME))
            ssh_inst.ssh(
                'cd galahad/tests/integration && pytest {} {} --setup-show --html=integration-test-report.html '
                '--self-contained-html --junit-xml=integration-test-report.xml {}'.format(verbose_tag, profile_tag, args.run_test))

        if args.run_all_tests:

            logger.info(
                '\n!!!!!!!!!\nRunning Tests on excalibur server [{}]\n!!!!!!!!!!'.
                    format(EXCALIBUR_HOSTNAME))

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
