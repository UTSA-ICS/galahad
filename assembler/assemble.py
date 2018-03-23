#!/usr/bin/env python

# Python script to take in a cloud-init type user-data yaml file, and modify it
# Such that upon boot, the system will be modified to run a docker container with
# Some security policies

# 2018 Raytheon BBN Technologies 
# Author: Stanislav Ponomarev stanislav.ponomarev@raytheon.com

import sys, os, argparse, yaml, base64, crypt, subprocess

CLOUD_INIT_SOURCE_USER_FILE = 'cloud-init.user-data'
CLOUD_INIT_SOURCE_META_FILE = 'cloud-init.meta-data'
OUTPUT_ISO_NAME = 'virtue.cloud-init.iso'

class CloudInitConfig():
    def __init__(self):
        self.userdata = {'repo-update': True}
        self.metadata = {'local-hostname': 'hostname', 'instance-id': 'id-01'}


    def copy_file(self, local_path, remote_path, permissions='0666', owner='root:root'):
        with open(local_path, 'rb') as f:
            #encoded_file = base64.b64encode(f.read())
            encoded_file = f.read()
        if 'write_files' not in self.userdata:
            self.userdata['write_files'] = []
        self.userdata['write_files'].append({ 'path': remote_path, \
                    'permissions': permissions, \
                    'owner': owner, \
                    'content': encoded_file, \
                    })

    def create_user(self, name, password, sudo='ALL=(ALL) ALL', shell='/bin/bash', lock_passwd=False, groups=None):
        entry = {'name': name, 'passwd': crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))}
        if sudo != None:
            entry['sudo'] = sudo
        if shell != None:
            entry['shell'] = shell
        if lock_passwd != None:
            entry['lock_passwd'] = lock_passwd
        if groups != None:
            entry['groups'] = groups
        if 'users' not in self.userdata:
            self.userdata['users'] = []
        self.userdata['users'].append(entry)

    def install_package(self, name):
        if 'packages' not in self.userdata.keys():
            self.userdata['packages'] = []
        self.userdata['packages'].append(name)

    def add_group(self, name):
        if 'groups' not in self.userdata.keys():
            self.userdata['groups'] = []
        self.userdata['groups'].append(name)

    def run_cmd(self, cmd):
        if 'runcmd' not in self.userdata.keys():
            self.userdata['runcmd'] = []
        self.userdata['runcmd'].append(cmd)
        

    def save(self):
        print("Saving user-data...")
        with open('user-data', 'w') as f:
            f.write('#cloud-config\n')
            yaml.dump(self.userdata, f)

        print("Saving meta-data...")
        with open('meta-data', 'w') as f:
            yaml.dump(self.metadata, f)

        print("Done.")
        


if __name__ == "__main__":
    #parser = argparse.ArgumentParser(description="Generate cloud-init's user-data and meta-data for Virtue")
    #parser.add_argument('--image', required=True, metavar='TARBALL', help='Tarball of Docker image')
    #parser.add_argument('--start-cmd', required=True, metavar='"CMD"', help='Command to start docker container')
    #parser.add_argument('--apparmor', required=True, help='AppArmor profile file')
    #parser.add_argument('--seccomp', required=True, help='Seccomp profile file')
    #parser.add_argument('--iso', action='store_true', help='Generate clod-init config CD-ROM image')
    #args = parser.parse_args()
  
    config = CloudInitConfig()
    config.install_package('docker.io')
    config.create_user('virtue', 'virtue')
    config.run_cmd(['cat', '/etc/shadow'])
    config.save()


    if True:
        print("Generating iso image "+OUTPUT_ISO_NAME+"...")
        subprocess.call(['mkisofs', '-output', OUTPUT_ISO_NAME, '-volid', 'cidata', '-joliet', '-rock', 'user-data', 'meta-data'])
        print("Done.")
        

