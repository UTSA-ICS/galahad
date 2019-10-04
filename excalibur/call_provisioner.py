#!/usr/bin/python

# Copyright (c) 2019 by Star Lab Corp.

import argparse

from assembler.assembler import Assembler


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u',
                        '--username',
                        type=str,
                        required=True,
                        help='Username of virtue owner')
    parser.add_argument('-i',
                        '--virtue_id',
                        type=str,
                        required=True,
                        help='ID of the newly provisioned virtue')
    parser.add_argument('-b',
                        '--base_img',
                        type=str,
                        required=True,
                        help=('The path to the unprovisioned virtue image. '
                              'Format must be mountable'))
    parser.add_argument('-o',
                        '--output_path',
                        type=str,
                        required=True,
                        help=('Where to put the provisioned Virtue image. '
                              'Existing file will be overwritten'))
    parser.add_argument('-v',
                        '--virtue_key',
                        type=str,
                        required=True,
                        help="The Virtue's private key")
    parser.add_argument('-e',
                        '--excalibur_key',
                        type=str,
                        required=True,
                        help="Excalibur's public key")
    parser.add_argument('--user_key',
                        type=str,
                        required=True,
                        help="The user's public SSH key")
    parser.add_argument('-r',
                        '--rethinkdb_cert',
                        type=str,
                        required=True)
    parser.add_argument('-n',
                        '--network_rules',
                        type=str,
                        required=True,
                        help='file containing network rules for the virtue')

    args = parser.parse_args()

    return args


if (__name__ == '__main__'):

    args = parse_args()

    assembler = Assembler()
    assembler.provision_virtue(args.username,
                               args.virtue_id,
                               args.base_img,
                               args.output_path,
                               args.virtue_key,
                               args.excalibur_key,
                               args.user_key,
                               args.rethinkdb_cert,
                               args.network_rules)
