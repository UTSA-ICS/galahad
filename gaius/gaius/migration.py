#!/usr/bin/env python
import subprocess
import sys
import os

class Migrate():
        def start_instance(self, host, guestnet, valor_guestnet):
                print subprocess.Popen("bin/new_cfg.sh " + host + " " + guestnet + " " + valor_guestnet, shell=True, stdout=subprocess.PIPE).stdout.read()
        def migrate_instance(self, host, location):
                print subprocess.Popen("bin/migrate.sh " + host + " " + location, shell=True, stdout=subprocess.PIPE).stdout.read()
        def cleanup_instance(self, host):
                print subprocess.Popen("bin/cleanup.sh " + host, shell=True, stdout=subprocess.PIPE).stdout.read()
