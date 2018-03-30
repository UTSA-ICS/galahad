#!/usr/bin/env python

# Generates cloud-init style yaml files that can be passed to a VM for proper config
# Author: Stanislav Ponomarev
# Email: stanislav.ponomarev@raytheon.com

import yaml, random, string, argparse, os, subprocess

REMOTE_SCRIPT='''
#!/bin/bash

docker ps
while [ $? -ne 0 ]; do
    echo "Waiting for docker"
    sleep 1
    docker ps
done
python3 --version
while [ $? -ne 0 ]; do
    echo "Waiting for python"
    sleep 1
    python3 --version
done
pip3 --version
while [ $? -ne 0 ]; do
    echo "Waiting for pip"
    sleep 1
    pip3 --version
done
service docker restart
pip3 install docker
%s
cd /root
tar xzf pack.tar.gz
rm $0 # delete the password
./run.py -p start %s
'''


class CloudInitUserData():
    ''' Generates two yaml-like files for cloud-init startup
        FYI Clud-init looks for these files in different sources. One such source
        is a cd-rom. It's common to build an iso that contains these files to 
        pass to a vm.
    '''
    def __init__(self, app_name):
        self.userdata = {'ssh_pwauth': True, 'repo_update': True}
        self.metadata = {}
        self._generate_metadata(app_name)
    
    def _ensure_key_exists(self, key, init_value = {}):
        if key not in self.userdata:
            self.userdata[key] = init_value

    def _generate_metadata(self, app_name):
        id_str = ''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(16))
        self.metadata['local-hostname'] = 'virtue-'+app_name+'-'+id_str
        self.metadata['instance-id'] = 'instance-'+id_str
        

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

    def save(self):
        with open('user-data', 'w') as f:
            f.write("#cloud-config\n")
            f.write(yaml.dump(self.userdata))
        with open('meta-data', 'w') as f:
            f.write(yaml.dump(self.metadata))
        



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate CloudInit data for virtue vm')
    parser.add_argument('-d', '--docker-virtue', help='Path to Galahad Docker-Virtue virtue folder')
    parser.add_argument('-l', '--docker-login', help='docker login command as a single string to login the docker registry')
    parser.add_argument('container_name', nargs=1, help='What docker-virtue container to run on start')
    args = parser.parse_args()

    ci = CloudInitUserData(args.container_name[0])
    ci.install_package('docker.io')
    ci.install_package('python3')
    ci.install_package('python3-pip')

    key = 0
    with open("id_rsa.pub", 'r') as f:
        key = f.read()
    ci.add_user('virtue', key)

    cwd = os.getcwd()
    os.chdir(args.docker_virtue)
    cmd = ['./run.py', '-r']
    cmd.extend(['pack', args.container_name[0]])
    print(' '.join(cmd))
    subprocess.check_call(cmd)
    os.chdir(cwd)


    ci.write_files(REMOTE_SCRIPT % (args.docker_login, args.container_name[0]), '/root/remote_script.sh', permissions='0700')
    ci.write_files(os.path.join(args.docker_virtue, args.container_name[0]+'.tar.gz'), '/root/pack.tar.gz', permissions='0600')
    ci.run_cmd(['/root/remote_script.sh'])
    ci.save()
