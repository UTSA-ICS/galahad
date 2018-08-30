#!/usr/bin/env python
import subprocess
import sys
import os

class Migrate():
    def start_instance(self, host, guestnet, valor_guestnet, efs_path):
        print(subprocess.Popen("gaius/bin/new_cfg.sh " + ' '.join([host, guestnet,
                                                                   valor_guestnet,
                                                                   efs_path]),
                               shell=True, stdout=subprocess.PIPE).stdout.read())

    def migrate_instance(self, host, location):
        print(subprocess.Popen("gaius/bin/migrate.sh " + host + " " + location,
                               shell=True, stdout=subprocess.PIPE).stdout.read())

    def cleanup_instance(self, host):
        print(subprocess.Popen("gaius/bin/cleanup.sh " + host,
                               shell=True, stdout=subprocess.PIPE).stdout.read())
