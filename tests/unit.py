#!/usr/bin/python

# Copyright (c) 2019 by Star Lab Corp.

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
        '--run_test',
        type=str,
        help='The specified Unit Test that will be run')

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

    ssh_inst = ssh_tool('ubuntu', EXCALIBUR_HOSTNAME, sshkey=args.sshkey)

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
                         '--html=unit-test-report.html --self-contained-html ' 
                         '--junit-xml=unit-test-report.xml'.format(verbose_tag, profile_tag))

        if args.run_test:

            logger.info(
                '\n!!!!!!!!!\nRun Test on excalibur server [{}]\n!!!!!!!!!!'.
                    format(EXCALIBUR_HOSTNAME))

            ssh_inst.ssh('cd galahad/tests/unit && pytest --durations=0 --setup-show  {} {} --html=unit-test-report.html '
                         '--self-contained-html --junit-xml=unit-test-report.xml {}'.format(verbose_tag, profile_tag, args.run_test))

        if args.run_all_tests:

            ssh_inst.ssh('cd galahad/tests/unit && pytest {} {}  --durations=0 --setup-show --html=unit-test-report.html '
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
