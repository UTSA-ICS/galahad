#!/usr/bin/python

import argparse

from assembler.assembler import Assembler

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b',
                        '--base_img',
                        type=str,
                        required=True,
                        help=('The path to the unprovisioned virtue image. '
                              'Format must be mountable'))
    parser.add_argument('-p',
                        '--ssh_pub_key',
                        type=str,
                        required=True,
                        help="The Virtue's private key")
    parser.add_argument('-o',
                        '--output_path',
                        type=str,
                        required=True,
                        help=('Where to put the provisioned Virtue image. '
                              'Existing file will be overwritten'))
    parser.add_argument('-e',
                        '--elastic_node',
                        type=str,
                        required=False,
                        help='Elastic Node to use')
    parser.add_argument('-s',
                        '--syslog_server',
                        type=str,
                        required=False,
                        help='Syslog Server address')
    parser.add_argument('-r',
                        '--rethink_host',
                        type=str,
                        required=False,
                        help='RethinkDB address')
    parser.add_argument('-w',
                        '--work_dir',
                        type=str,
                        required=False,
                        help='Path to use as a temporary work directory. Does not have to exist.')

    args = parser.parse_args()

    return args

if (__name__ == '__main__'):

    args = parse_args()

    build_options = {
        'env': 'xen',
        'base_img': args.base_img,
        'ssh_key': args.ssh_pub_key,
        'output_path': args.output_path
    }

    kwargs = {}
    if (args.elastic_node != None):
        kwargs['es_node'] = args.elastic_node
    if (args.syslog_server != None):
        kwargs['syslog_server'] = args.syslog_server
    if (args.rethink_host != None):
        kwargs['rethinkdb_host'] = args.rethink_host
    if (args.work_dir != None):
        kwargs['work_dir'] = args.work_dir

    assembler = Assembler(**kwargs)
    assembler.construct_unity(build_options,
                              clean=True)
