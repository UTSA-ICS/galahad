# Copyright (c) 2018 by Raytheon BBN Technologies Corp.
# Copyright (c) 2019 by Star Lab Corp.

import os
import shutil
import subprocess
import time
from urllib3.util import parse_url

from .ssh_tool import ssh_tool

AGGREGATOR_HOSTNAME = 'aggregator.galahad.com'
RETHINKDB_HOSTNAME = 'rethinkdb.galahad.com'

class Assembler(object):

    def __init__(self,
                 es_node='https://{}:9200'.format(AGGREGATOR_HOSTNAME),
                 syslog_server='192.168.4.10',
                 rethinkdb_host=RETHINKDB_HOSTNAME,
                 work_dir='tmp'):
        self.elastic_search_node = es_node
        self.elastic_search_host = parse_url(es_node).host
        self.syslog_server = syslog_server
        self.rethinkdb_host = rethinkdb_host
        self.work_dir = work_dir # where all the generated files will live

    def construct_img(self, base_img, work_dir, payload_dir, ssh_key=None):

        # Create image
        shutil.copy(base_img, work_dir + '/disk.img')

        # Mount the image
        mount_path = work_dir + '/img_mount'
        print('Image created. Mounting at ' + mount_path + '\n')
        if (not os.path.exists(mount_path)):
            os.makedirs(mount_path)

        subprocess.check_call(['mount',
                               '{0}/disk.img'.format(work_dir),
                               mount_path])

        real_HOME = os.environ['HOME']
        os.environ['DEBIAN_FRONTEND'] = 'noninteractive'

        try:

            # chroot doesn't change the $HOME environment variable
            os.environ['HOME'] = '/home/virtue'
            virtue_home = mount_path + os.environ['HOME']

            # dpkg wants a cpuinfo file and transducers want a procfs to
            #   install java
            mount_proc_cmd = ['mount', '-t', 'proc',
                              'proc', mount_path + '/proc']
            subprocess.check_call(mount_proc_cmd)
            mount_sys_cmd = ['mount', '-t', 'sysfs',
                              'sys', mount_path + '/sys']
            subprocess.check_call(mount_sys_cmd)
            mount_dev_cmd = ['mount', '-o', 'bind',
                              '/dev', mount_path + '/dev']
            subprocess.check_call(mount_dev_cmd)

            # If the Ubuntu image wasn't created on the same network,
            # resolv.conf may have the wrong nameserver set. This nameserver
            # will be wiped when the VM is launched.
            with open(mount_path + '/etc/resolv.conf', 'w') as resolv:
                resolv.write('nameserver 8.8.8.8')

            # Update installed packages
            subprocess.check_call(['chroot', mount_path, 'apt-get',
                                   'update'])
            subprocess.check_call(['chroot', mount_path, 'apt-get',
                                   'dist-upgrade', '-y'])

            # Install required packages
            # Note: To install the latest version of Docker, see
            #       https://docs.docker.com/install/linux/docker-ce/ubuntu/
            apt_cmd = ['chroot', mount_path, 'apt-get', 'install', '-y']
            apt_cmd.extend(['python', 'python-pip',
                            'python3', 'python3-pip',
                            'git',
                            'docker.io',
                            'wget',
                            'perl',
                            'software-properties-common',
                            'openssh-server',
                            'auditd',
                            'dkms',
                            'psmisc',
                            'krb5-user',
                            'cifs-utils',
                            'smbclient',
                            'nfs-common'])
            subprocess.check_call(apt_cmd)

            # Install all .deb packages with dpkg --root
            merlin_file_path = os.path.join(real_HOME, 'galahad',
                                            'transducers')
            processkiller_file_path = os.path.join(real_HOME, 'galahad',
                                            'transducers')
            ossensor_file_path = os.path.join(real_HOME, 'galahad',
                                            'transducers')
            kernel_file_path = os.path.join(real_HOME, 'galahad',
                                            'unity', 'latest-debs')

            merlin_files = ['merlin.deb']
            processkiller_files = ['processkiller.deb']
            ossensor_files = ['ossensor.deb']

            kernel_files = [
                'linux-headers-4.13.0-46_4.13.0-46.51+unity1_all.deb',
                'linux-headers-4.13.0-46-generic_4.13.0-46.51+unity1_amd64.deb',
                'linux-image-4.13.0-46-generic_4.13.0-46.51+unity1_amd64.deb'
            ]

            files = []
            for f in merlin_files:
                f = os.path.join(merlin_file_path, f)
                files.append(f)
            for f in processkiller_files:
                f = os.path.join(processkiller_file_path, f)
                files.append(f)
            for f in ossensor_files:
                f = os.path.join(ossensor_file_path, f)
                files.append(f)
            for f in kernel_files:
                f = os.path.join(kernel_file_path, f)
                files.append(f)

            dpkg_cmd = ['dpkg', '-i', '--force-all',
                        '--root=' + mount_path]
            dpkg_cmd.extend(files)
            subprocess.check_call(dpkg_cmd)

            # Additional Merlin config
            os.chown(mount_path + '/opt/merlin', 501, 1000)
            for path, dirs, files in os.walk(mount_path + '/opt/merlin'):
                for f in files:
                    os.chown(os.path.join(path, f), 501, 1000)
                for d in dirs:
                    os.chown(os.path.join(path, d), 501, 1000)

            os.chmod(mount_path + '/opt/merlin', 0o777)
            
            # Make Merlin own the OS Sensor config file
            with open(mount_path + '/opt/ossensor/ossensor-config.json', 'w+') as f:
                f.write("{}")
                
            os.chown(mount_path + '/opt/ossensor/ossensor-config.json', 501, 1000)

            os.chown(mount_path + '/var/private/ssl', 501, 1000)
            for path, dirs, files in os.walk(mount_path + '/var/private/ssl'):
                for f in files:
                    os.chown(os.path.join(path, f), 501, 1000)
                for d in dirs:
                    os.chown(os.path.join(path, d), 501, 1000)

            # Disable merlin until the virtue-id is populated
            subprocess.check_call(['chroot', mount_path,
                                   'systemctl', 'disable', 'merlin'])

            # Enable processkiller
            subprocess.check_call(['chroot', mount_path,
                                   'systemctl', 'enable', 'processkiller'])

            # Enable ossensor
            subprocess.check_call(['chroot', mount_path,
                                   'systemctl', 'enable', 'ossensor'])

            # Add users
            #     adduser virtue --system --group --shell /bin/bash
            virtue_line = 'virtue:x:500:500::/home/virtue:/bin/bash\n'
            gvirtue_line = 'virtue:x:500:\n'
            svirtue_line = 'virtue:*:17729:0:99999:7:::\n'
            gsvirtue_line = 'virtue:!::\n'

            #     adduser merlin --system --group --shell /bin/bash
            merlin_line = 'merlin:x:501:501::/home/merlin:/bin/bash\n'
            gmerlin_line = 'merlin:x:501:\n'
            smerlin_line = 'merlin:*:17729:0:99999:7:::\n'
            gsmerlin_line = 'merlin:!::\n'

            gcamelot_line = 'camelot:x:1000:merlin,root\n'
            gscamelot_line = 'camelot:!::merlin,root\n'

            bashrc_line = 'export TERM=xterm-256color\n'

            sudoers_line = 'virtue ALL=(ALL) NOPASSWD:ALL\n'

            with open(mount_path + '/etc/passwd', 'a') as passwd:
                passwd.write(virtue_line)
                passwd.write(merlin_line)
            with open(mount_path + '/etc/group', 'a') as group:
                group.write(gvirtue_line)
                group.write(gmerlin_line)
                group.write(gcamelot_line)
            with open(mount_path + '/etc/shadow', 'a') as shadow:
                shadow.write(svirtue_line)
                shadow.write(smerlin_line)
            with open(mount_path + '/etc/gshadow', 'a') as gshadow:
                gshadow.write(gsvirtue_line)
                gshadow.write(gsmerlin_line)
                gshadow.write(gscamelot_line)

            with open(mount_path + '/etc/sudoers', 'a') as sudoers:
                sudoers.write(sudoers_line)

            os.makedirs(mount_path + '/home/virtue/.ssh')
            os.makedirs(mount_path + '/home/merlin/.ssh')

            with open(mount_path + '/home/virtue/.bashrc', 'w') as bashrc:
                bashrc.write(bashrc_line)
            with open(mount_path + '/home/merlin/.bashrc', 'w') as bashrc:
                bashrc.write(bashrc_line)

            # Add public ssh key to /home/*/.ssh/authorized_hosts
            ssh_key_path = work_dir + '/id_rsa.pub'
            if (ssh_key):
                ssh_key_path = ssh_key

            shutil.copy(ssh_key_path,
                        mount_path + '/home/virtue/.ssh/authorized_keys')
            shutil.copy(ssh_key_path,
                        mount_path + '/home/merlin/.ssh/authorized_keys')

            # Copy the certs required for connection to elasticsearch
            # These certs will be used by syslog-ng service
            # Copy the certs from galahad-keys dir.
            shutil.copy(
                os.path.join(real_HOME, 'galahad-keys') + '/kirk-keystore.jks',
                virtue_home)
            shutil.copy(
                os.path.join(real_HOME, 'galahad-keys') + '/truststore.jks',
                virtue_home)

            # Install Transducers
            # Copy files from payload dir to mount_path + '/home/virtue'
            shutil.copy(payload_dir + '/transducer-module.tar.gz',
                        virtue_home)
            shutil.copy(payload_dir + '/sshd_config',
                        virtue_home)
            shutil.copy(payload_dir + '/runme.sh',
                        virtue_home)
            shutil.copy(payload_dir + '/syslog-ng.service',
                        virtue_home)
            shutil.copy(payload_dir + '/audit.rules',
                        virtue_home)

            # Create syslog-ng.conf from
            #   payload/syslog-ng-virtue-node.conf.template
            with open(payload_dir + '/syslog-ng-virtue-node.conf.template',
                      'r') as t:
                syslog_ng_config = t.read()
                with open(virtue_home + '/syslog-ng.conf', 'w') as f:
                    f.write(syslog_ng_config % (self.elastic_search_node,
                                                self.syslog_server))
            # Create elasticsearch.yml from ELASTIC_YML
            with open(payload_dir + '/elasticsearch.yml.template', 'r') as t:
                elastic_yml = t.read()
                with open(virtue_home + '/elasticsearch.yml',
                          'w') as f:
                    f.write(elastic_yml % (self.elastic_search_host))

            # Execute runme.sh with chroot
            os.chmod(virtue_home + '/runme.sh', 0o775)
            runme_cmd = ['chroot', mount_path, 'bash', '-c',
                         'cd \"/home/virtue\" && ./runme.sh']
            subprocess.check_call(runme_cmd)

            # Install Actuators
            actuator_file_path = os.path.join(payload_dir, 'actuators')
            actuator_files = ['netblock_actuator.deb']
            files = []
            for f in actuator_files:
                f = os.path.join(actuator_file_path, f)
                files.append(f)

            dpkg_cmd = ['dpkg', '-i', '--force-all', '--root=' + mount_path]
            dpkg_cmd.extend(files)

            subprocess.check_call(dpkg_cmd)

            # Additional actuator config
            shutil.copy(mount_path + '/lib/modules/4.13.0-46-generic' +
                        '/updates/dkms/actuator_network.ko',
                        mount_path + '/lib/modules/4.13.0-46-generic' +
                        '/kernel/drivers/')

            with open(mount_path + '/etc/modules', 'a') as modules:
                modules.write('actuator_network\n')

            # Additional Process Killer config
            os.chown(mount_path + '/opt/merlin', 501, 1000)
            for path, dirs, files in os.walk(mount_path + '/opt/merlin'):
                for f in files:
                    os.chown(os.path.join(path, f), 501, 1000)
                for d in dirs:
                    os.chown(os.path.join(path, d), 501, 1000)


            # Install the unity-net service for Valor networking
            shutil.copy(payload_dir + '/unity-net.service',
                        mount_path + '/etc/systemd/system')
            shutil.copy(payload_dir + '/unity-net.sh',
                        mount_path + '/root/')

            subprocess.check_call(['chroot', mount_path,
                                   'systemctl', 'enable', 'unity-net.service'])

            os.chmod(mount_path + '/root/unity-net.sh', 0o744)

            subprocess.check_call(['chroot', mount_path,
                                   'sed', '-i', '/.*eth0.*/d',
                                   '/etc/network/interfaces'])

            # Reset ownership in user directories
            os.chown(mount_path + '/home/virtue', 500, 500)
            for path, dirs, files in os.walk(mount_path + '/home/virtue'):
                for f in files:
                    os.chown(os.path.join(path, f), 500, 500)
                for d in dirs:
                    os.chown(os.path.join(path, d), 500, 500)

            os.chown(mount_path + '/home/merlin', 501, 501)
            for path, dirs, files in os.walk(mount_path + '/home/merlin'):
                for f in files:
                    os.chown(os.path.join(path, f), 501, 501)
                for d in dirs:
                    os.chown(os.path.join(path, d), 501, 501)

        except:
            raise
        finally:

            os.environ['HOME'] = real_HOME

            subprocess.call(['umount', mount_path + '/proc'])
            subprocess.call(['umount', mount_path + '/sys'])
            subprocess.call(['umount', mount_path + '/dev'])
            subprocess.check_call(['umount', mount_path])

    def construct_unity(self, base_img, output_path, ssh_key=None, clean=False):

        WORK_DIR = self.work_dir

        if os.path.exists(WORK_DIR) and os.listdir(WORK_DIR) != []:
            print("Cleaning working directory...")
            shutil.rmtree(WORK_DIR)

        if not os.path.exists(WORK_DIR):
            os.mkdir(WORK_DIR)

        if (not ssh_key):
            subprocess.check_call(['ssh-keygen', '-N', '', '-f',
                                   WORK_DIR + '/id_rsa'])

        # Build the merlin deb file
        subprocess.check_call(os.path.join(os.environ['HOME'], 'galahad',
                                           'transducers', 'build_merlin.sh'))
        # Build the processkiller deb file
        subprocess.check_call(os.path.join(os.environ['HOME'], 'galahad',
                                           'transducers', 'build_processkiller.sh'))
        # Build the ossensor deb file
        subprocess.check_call(os.path.join(os.environ['HOME'], 'galahad',
                                           'transducers', 'build_ossensor.sh'))

        self.construct_img(base_img, WORK_DIR,
                           os.path.join(os.environ['HOME'],
                                        'galahad',
                                        'assembler',
                                        'payload'),
                           ssh_key=ssh_key)

        print("Constructor is done")

        output_dir = output_path
        if (ssh_key):
            output_dir = os.path.dirname(output_path)

        if (not os.path.exists(output_dir)):
            os.makedirs(output_dir)

        if (clean):
            move = shutil.move
        else:
            move = shutil.copy

        move(os.path.join(WORK_DIR, 'disk.img'), output_path)

        if (not ssh_key):
            move(os.path.join(WORK_DIR, 'id_rsa'), output_dir)
            move(os.path.join(WORK_DIR, 'id_rsa.pub'), output_dir)

        if (clean):
            shutil.rmtree(WORK_DIR)

    def assemble_running_vm(self, containers, docker_login, key_path,
                            ssh_host):

        USER_SCRIPT = '''#!/bin/bash
        cd /home/virtue
        mkdir {0}
        pip3 install --user docker pyyaml
        git clone https://github.com/starlab-io/docker-virtue.git
        cd docker-virtue/virtue
        sudo {1}
        sudo ./run.py -p start {0}
        cd /home/virtue
        sudo rm -rf docker-virtue
        '''

        ssh = ssh_tool('virtue', ssh_host, key_path)
        assert ssh.check_access()

        ssh.ssh(USER_SCRIPT.format(' '.join(containers), docker_login))


    def provision_virtue(self,
                         username,
                         virtue_id,
                         img_path,
                         output_path,
                         virtue_key, # The Virtue's private key
                         excalibur_key, # Excalibur's public key
                         rethinkdb_cert, #RethinkDB's SSL cert
                         networkRules):

        image_mount = '{0}/{1}'.format(os.environ['HOME'], virtue_id)
        os.mkdir(image_mount)

        try:

            subprocess.check_call(['mount',
                                   output_path,
                                   image_mount])

            with open(image_mount + '/etc/virtue-id', 'w') as id_file:
                id_file.write(virtue_id)

            with open(image_mount + '/etc/virtue-id-env', 'w') as id_file:
                id_file.write("VIRTUE_ID=" + str(virtue_id))

            # Enable merlin since virtue-id is now available
            subprocess.check_call(['chroot', image_mount,
                                   'systemctl', 'enable', 'merlin'])

            # read network rules
            rules = ""
            with open(networkRules, 'r') as networkRulesFile:
                rules += networkRulesFile.read()

            # echo network rules to a file on the virtue
            with open(image_mount + '/etc/networkRules', 'w+') as iprules_file:
                iprules_file.write(rules)

            # delete network rules file from excalibur
            os.remove(networkRules)

            if (not os.path.exists(image_mount + '/var/private/ssl')):
                os.makedirs(image_mount + '/var/private/ssl')

            with open(image_mount + '/var/private/ssl/virtue_1_key.pem',
                      'w') as virtue_1_key:
                virtue_1_key.write(virtue_key)
            with open(image_mount + '/var/private/ssl/excalibur_pub.pem',
                      'w') as excalibur_pub:
                excalibur_pub.write(excalibur_key)
            with open(image_mount + '/var/private/ssl/rethinkdb_cert.pem',
                      'w') as rethinkdb_cert_file:
                rethinkdb_cert_file.write(rethinkdb_cert)

            os.chown(image_mount + '/var/private', 501, 500)
            for path, dirs, files in os.walk(image_mount + '/var/private'):
                for f in files:
                    os.chown(os.path.join(path, f), 501, 500)
                    os.chmod(os.path.join(path, f), 0o700)
                for d in dirs:
                    os.chown(os.path.join(path, d), 501, 500)
                    os.chmod(os.path.join(path, d), 0o700)

            # KL --- configure krb5.conf file
            with open(image_mount + '/etc/hosts', 'a') as hosts:
                hosts.write("172.30.1.250 camelot.virtue.gov")

            krb5_conf_src = '/etc/krb5.conf'
            krb5_conf_dest = "{}{}".format(image_mount, krb5_conf_src)
            shutil.copyfile(krb5_conf_src, krb5_conf_dest)

            # KL --- move to virtue launch. tmp is overwritten when restarted :facepalm:
            krb5cc_src = '/tmp/krb5cc_{}'.format(username)
            krb5cc_dest = '{}/tmp/krb5cc_0'.format(image_mount)
            print("WAT:    {}    {}".format(krb5cc_src, krb5cc_dest))
            print(shutil.copyfile(krb5cc_src, krb5cc_dest))

        except:
            os.remove(output_path)
            raise
        finally:
            subprocess.call(['umount', image_mount])
            os.rmdir(image_mount)
