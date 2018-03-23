#!/usr/bin/env python

import yaml


class CloudInitUserData():
    def __init__(self):
        self.userdata = {'ssh_pwauth': True, 'repo_update': True}
        self.metadata = {'instance-id': 'test-assembler-local-01', 'local-hostname': 'assembler-test-vm'}
    
    def _ensure_key_exists(self, key, init_value = {}):
        if key not in self.userdata:
            self.userdata[key] = init_value

    def install_package(self, package):
        key = 'packages'
        self._ensure_key_exists(key, [])
        if package not in self.userdata[key]:
            self.userdata[key].append(package)

    def add_user(self, username, ssh_authorized_keys=None, sudo='ALL=(ALL) NOPASSWD:ALL', shell='/bin/bash'):
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
        self.userdata[key].append(new_entry)

    def write_files(self, source, destination, owner=None, permissions=None):
        key='write_files'
        self._ensure_key_exists(key, [])
        entry = {}
        entry['path'] = destination
        with open(source, 'rb') as f:
            entry['content'] = f.read()
        if owner is not None:
            entry['owner'] = owner
        if permissions is not None:
            entry['permissions'] = permissions
        self.userdata[key].append(entry)

    def run_cmd(self, cmd):
        key='runcmd'
        self._ensure_key_exists(key, [])
        self.userdata[key].append(cmd)

    #def grow_part(self, dev):
    #    key='growpart'
    #    self._ensure_key_exists(key, [])
    #    entry = {'mode': 'auto'}
    #    entry['devices'] = [dev]



    def save(self):
        with open('user-data', 'w') as f:
            f.write("#cloud-config\n")
            f.write(yaml.dump(self.userdata))
        with open('meta-data', 'w') as f:
            f.write(yaml.dump(self.metadata))
        



if __name__ == '__main__':
    ci = CloudInitUserData()

    ci.install_package('docker.io')

    key = 0
    with open("id_rsa.pub", 'r') as f:
        key = f.read()
    ci.add_user('virtue', key)

    ci.write_files('remote_script.sh', '/root/remote_script.sh', permissions='0700')
    ci.run_cmd('/root/remote_script.sh')
    ci.save()
