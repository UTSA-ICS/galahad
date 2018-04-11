#!/usr/bin/env python

# Generates cloud-init style yaml files that can be passed to a VM for proper config
# Author: Stanislav Ponomarev
# Email: stanislav.ponomarev@raytheon.com

import yaml, random, string, os, subprocess


class CloudInitUserData():
    ''' Generates two yaml-like files for cloud-init startup
        FYI Clud-init looks for these files in different sources. One such source
        is a cd-rom. It's common to build an iso that contains these files to 
        pass to a vm.
    '''
    USERDATA_FILENAME = 'user-data'
    METADATA_FILENAME = 'meta-data'

    def __init__(self):
        self.userdata = {'ssh_pwauth': True, 'repo_update': True}
        self.metadata = {}
    
    def _ensure_key_exists(self, key, init_value = {}):
        if key not in self.userdata:
            self.userdata[key] = init_value

    def _set_metadata(self, host_name, instance_id):
        self.metadata['local-hostname'] = host_name
        self.metadata['instance-id'] = instance_id
        

    def install_package(self, package):
        key = 'packages'
        self._ensure_key_exists(key, [])
        if package not in self.userdata[key]:
            self.userdata[key].append(package)

    def add_user(self, username, ssh_authorized_keys=None, groups=None, sudo='ALL=(ALL) NOPASSWD:ALL', shell='/bin/bash'):
        key = 'users'
        self._ensure_key_exists(key, [])
        for entry in self.userdata[key]:
            if 'name' in entry and entry['name'] == username:
                raise Exception("User name %s is already registered in cloud-init" % (username))
        new_entry = {'name': username}
        if ssh_authorized_keys is not None:
            new_entry['ssh-authorized-keys'] = ssh_authorized_keys
        if sudo is not None:
            new_entry['sudo'] = sudo
        if shell is not None:
            new_entry['shell'] = shell
        if groups is not None:
            new_entry['groups'] = groups
        self.userdata[key].append(new_entry)

    def add_group(self, new_group, members=[]):
        key = 'groups'
        self._ensure_key_exists(key, [])
    
        new_entry = ''
        if len(members) == 0:
            new_entry = new_group
        else:
            new_entry = {new_group: members}

        self.userdata[key].append(new_entry)

    def write_files(self, source, destination, owner=None, permissions=None):
        key='write_files'
        self._ensure_key_exists(key, [])
        entry = {}
        entry['path'] = destination
        # decide if source is a file path or a script text
        if '\n' in source: # if there are new lines, this is not a path
            entry['content'] = source
        elif os.path.isfile(source): # if it's a single line, see if file exists
            with open(source, 'rb') as f:
                entry['content'] = f.read()
        else: # not a file and a single line... one-liner I guess...
            entry['content'] = source

        if owner is not None:
            entry['owner'] = owner
        if permissions is not None:
            entry['permissions'] = permissions
        self.userdata[key].append(entry)

    def run_cmd(self, cmd):
        key='runcmd'
        self._ensure_key_exists(key, [])
        self.userdata[key].append(cmd)

    def save(self, out_dir):
        with open(os.path.join(out_dir, self.USERDATA_FILENAME), 'w') as f:
            f.write("#cloud-config\n")
            f.write(yaml.dump(self.userdata))
        with open(os.path.join(out_dir, self.METADATA_FILENAME), 'w') as f:
            f.write(yaml.dump(self.metadata))

    def load(self, in_dir):
        userdata_path = os.path.join(in_dir, self.USERDATA_FILENAME)
        metadata_path = os.path.join(in_dir, self.METADATA_FILENAME)
        with open(userdata_path, 'r') as f:
            self.userdata = yaml.load(f)
        with open(metadata_path, 'r') as f:
            self.metadata = yaml.load(f)

    def userdata_exists(self, in_dir):
        return os.path.exists(os.path.join(in_dir, self.USERDATA_FILENAME))

    def metadata_exists(self, in_dir):
        return os.path.exists(os.path.join(in_dir, self.METADATA_FILENAME))
    
