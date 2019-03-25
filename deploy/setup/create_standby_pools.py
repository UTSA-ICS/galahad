#!/usr/bin/env python

# Copyright (c) 2019 by Star Lab Corp.

import os
import sys
import argparse

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    (os.path.dirname(os.path.dirname(file_path)))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)

from website.valor import ValorManager
from website.controller import StandbyRoles


def create_valor_standby_pool():

    valor_manager = ValorManager()

    valor_manager.create_standby_valors()


def create_role_image_file_standby_pool(unity_image_size):

    new_role = {}

    # Create the role standby image files
    standby_roles = StandbyRoles(unity_image_size, new_role)

    standby_roles.create_standby_roles()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v',
                        '--valors',
                        action="store_true",
                        required=False,
                        help="Create standby valors.")
    parser.add_argument('-r',
                        '--role_image_files',
                        action="store_true",
                        required=False,
                        help="Create standby role image files. Please specify "
                             "unity_image_size option.")
    parser.add_argument('-u',
                        '--unity_image_size',
                        type=str,
                        required=False,
                        help="The unity image size for which standby pools "
                             "will be created")

    args = parser.parse_args()

    return args


if (__name__ == '__main__'):

    args = parse_args()

    if args.valors:
        create_valor_standby_pool()
    elif args.role_image_files and args.unity_image_size:
        create_role_image_file_standby_pool(args.unity_image_size)
    else:
        print("Incorrect parameters specified.\n"
              "Please specify the following options:\n"
              "--valors\n"
              "OR\n"
              "--role_image_files AND --unity_image_size")
