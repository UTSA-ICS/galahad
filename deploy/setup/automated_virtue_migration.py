#!/usr/bin/env python

import os
import sys
import argparse

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    (os.path.dirname(os.path.dirname(file_path)))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)

from website.valor import ValorAPI


def auto_migration_start(migration_interval):
    valor_api = ValorAPI()

    valor_api.auto_migration_start(migration_interval)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--migration_interval', default=300, type=int, required=False,
                        help="The interval at which automated migration of virtues "
                             "occurs")

    args = parser.parse_args()

    return args


if (__name__ == '__main__'):
    args = parse_args()

    auto_migration_start(args.migration_interval)
