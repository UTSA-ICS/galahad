# Copyright (c) 2018 by Star Lab Corp.
# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

import os, sys, shutil
import json, time
import subprocess
from urlparse import urlparse
import boto3
from collections import OrderedDict

from stages.core.ci_stage import CIStage
from stages.core.ssh_stage import SSHStage

from stages.kernel import KernelStage
from stages.shutdown import ShutdownStage
from stages.user import UserStage
from stages.apt import AptStage
from stages.virtued import DockerVirtueStage
from stages.transducer_install import TransducerStage
from stages.merlin import MerlinStage
from stages.actuator import ActuatorStage
from stages.processkiller import ProcessKillerStage

class Assembler(object):

    ISO_FILE = 'virtue.cloudinit.iso'
    LOG_FILE = 'SERIAL.log'

    NAME = ''

    def __init__(self,
                 #build_options,
                 #docker_login,
                 es_node='https://172.30.128.129:9200',
                 syslog_server='172.30.128.131',
                 rethinkdb_host='172.30.128.130',
                 work_dir='tmp'):
        #self.build_options = build_options
        #self.docker_login = docker_login
        self.elastic_search_node = es_node
        self.elastic_search_host = urlparse(es_node).hostname
        self.syslog_server = syslog_server
        self.rethinkdb_host = rethinkdb_host
        self.work_dir = work_dir # where all the generated files will live

    def start_aws_vm(self, image_id, instance_type, sec_group,
                     subnet, userdata, name, disk_size):
        print("Starting VM, %s" % (name))

        ec2 = boto3.resource('ec2')

        output = ec2.create_instances(
            ImageId=image_id,
            InstanceType=instance_type,
            KeyName='starlab-virtue-te',
            MinCount=1,
            MaxCount=1,
            Monitoring={'Enabled': False},
            SecurityGroupIds=[sec_group],
            SubnetId=subnet,
            UserData=userdata,
            BlockDeviceMappings=[{
                'DeviceName': '/dev/sda1',
                'Ebs': {
                    'VolumeSize': disk_size
                }
            }],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Project',
                            'Value': 'Virtue'
                        }
                    ]
                },
                {
                    'ResourceType': 'volume',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': name
                        }
                    ]
                }
            ])

        if len(output) > 0:
            print (output)
            instance = output[0]
            time.sleep(5)
            return instance.id
        else:
            print("Got unexpaced data")
            print(output)
            raise Exception("Can't start aws vm")

    def get_vm_ip(self, instanceId):
        cmd = ['aws', 'ec2', 'describe-instances', '--instance-ids', instanceId, '--query', 'Reservations[*].Instances[*].PublicIpAddress']
        print("Calling %s" % (' '.join(cmd)))
        is_vm_up = False
        while not is_vm_up:
            output = json.loads(subprocess.check_output(cmd).decode('utf-8'))
            if len(output) == 1 and len(output[0]) == 1:
                return output[0][0]
            elif len(output[0]) == 0:
                is_vm_up = False
            else:
                print("Got unexpected data")
                print(output)
                raise Exception("Can't get aws vm ip")

    def run_stage(self, stages, stage):
        for dep in stages[stage].DEPENDS:
            if dep not in stages.keys():
                raise ValueError("Stage %s depends on undefined stage %s" % (stage, dep))
            self.run_stage(stages, dep)
        stages[stage].run()


    # Deprecated and broken
    def setup_qemu(self, build_options, work_dir):
        if args.resize_img:
            # figure out image size by parsing output of 'qemu-img info $IMAGE'
            qemu_img = subprocess.Popen(['qemu-img', 'info', args.start_vm],
                                        stdout=subprocess.PIPE)
            qemu_img.wait()
            img_size = int(re.search('\(([0-9]+) bytes\)',
                                     str(qemu_img.stdout.read())).group(1))
            if img_size < 3000000000:
                subprocess.check_call(['qemu-img', 'resize', args.start_vm, args.resize_img])
        # create an iso with newly generated cloud-init data
        cwd = os.getcwd()
        os.chdir(WORK_DIR)
        cmd = ['mkisofs', '-output', ISO_FILE, '-volid', 'cidata', '-joliet', '-rock', 'user-data', 'meta-data']
        subprocess.check_call(cmd)
        os.chdir(cwd)
        iso_path = os.path.join(WORK_DIR, ISO_FILE)
        log_path = os.path.join(WORK_DIR, LOG_FILE)
        cmd = ['qemu-system-x86_64', '--enable-kvm', '-m', '1024', '-smp', '1', '-cdrom', iso_path, '-device', 'e1000,netdev=user.0', '-netdev', 'user,id=user.0,hostfwd=tcp::%s-:22' % (args.ssh_port), '-drive', 'file=%s,if=virtio,cache=writeback,index=0' % (args.start_vm), '-serial', 'file:%s' % (log_path)]

        vm = subprocess.Popen(cmd)

    # Deprecated
    def setup_aws(self, build_options, work_dir, vmname):
        #args.ssh_host = input("SSH host: ")
        #args.ssh_port = input("SSH port: ")
        '''Potentially can start AWS instance here instead. To launch new instance in starlab's environment last time this worked:
        aws ec2 run-instances --image-id ami-43a15f3e --count 1 --instance-type t2.micro --security-group-ids sg-0676d24f --subnet-id subnet-0b97b651 --iam-instance-profile "Name=Virtue-Tester" --user-data "$(cat tmp/user-data)" --tag-specifications "ResourceType=instance,Tags=[{Key=Project,Value=Virtue},{Key=Name,Value=BBN-Assembler}]"


        you can then get its IP address with

        aws ec2 describe-instances --instance-ids i-032d5f28b9281e42d --query "Reservations[*].Instances[*].PublicIpAddress"

        But somehow wrong tmp/user-data often ends up in the VM.

        Uploading user-data through a web-browser seems to also not work sometimes (maybe caching?)
        '''

        assert 'aws_image_id' in build_options.keys()
        assert 'aws_instance_type' in build_options.keys()
        assert 'aws_security_group' in build_options.keys()
        assert 'aws_subnet_id' in build_options.keys()
        assert 'aws_disk_size' in build_options.keys()

        if vmname == '':
            vmname = 'Unity'
        with open(os.path.join(work_dir, 'user-data'), 'r') as f:
            # Todo: Get aws_image_id by finding unity image
            instance = self.start_aws_vm(
                build_options['aws_image_id'],
                build_options['aws_instance_type'],
                build_options['aws_security_group'],
                build_options['aws_subnet_id'],
                f.read(),
                vmname,
                build_options['aws_disk_size'])
            print("New instance id: %s" % (instance))
            #return
            ssh_host = self.get_vm_ip(instance)
            print("New instance ip: %s" % (ssh_host))
            ssh_port = '22'
        print("Waiting for VM to start...")
        time.sleep(10)

        return (instance, ssh_host, ssh_port)

    def construct_img(self, build_options, work_dir, payload_dir):

        #assert 'img_size' in build_options.keys()
        assert 'base_img' in build_options.keys()

        # Create image
        img_name = 'Unity' + str(int(time.time()))
        #subprocess.check_call(['xen-create-image',
        #                       '--hostname=' + img_name,
        #                       '--dhcp',
        #                       '--dir=' + work_dir,
        #                       '--dist=xenial',
        #                       '--vcpus=1',
        #                       '--memory=1024MB',
        #                       '--genpass=0',
        #                       '--size={0}GB'.format(build_options['img_size'])])
        shutil.copy(build_options['base_img'],
                    work_dir + '/disk.img')
        # Mount the image
        mount_path = '/tmp/img_mount'
        print('Image created. Mounting at ' + mount_path + '\n')
        if (not os.path.exists(mount_path)):
            os.makedirs(mount_path)

        subprocess.check_call(['mount',
                               '{0}/disk.img'.format(work_dir),
                               mount_path])

        real_HOME = os.environ['HOME']

        try:

            # chroot doesn't change the $HOME environment variable
            os.environ['HOME'] = '/home/virtue'

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

            # Update installed packages
            subprocess.check_call(['chroot', mount_path, 'apt-get',
                                   'update'])
            subprocess.check_call(['chroot', mount_path, 'apt-get',
                                   'dist-upgrade', '-y'])

            # Install required packages
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
                            'dkms'])
            subprocess.check_call(apt_cmd)

            # Install all .deb packages with dpkg --root
            merlin_file_path = payload_dir
            kernel_file_path = os.path.join(real_HOME, 'galahad',
                                            'unity', 'latest-debs')
            merlin_files = ['merlin.deb']
            kernel_files = [
                'linux-headers-4.13.0-38_4.13.0-38.43+unity1_all.deb',
                'linux-image-4.13.0-38-generic_4.13.0-38.43+unity1_amd64.deb'
            ]

            files = []
            for f in merlin_files:
                f = os.path.join(merlin_file_path, f)
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

            os.chmod(mount_path + '/opt/merlin', 0777)

            os.chown(mount_path + '/var/private/ssl', 501, 1000)
            for path, dirs, files in os.walk(mount_path + '/var/private/ssl'):
                for f in files:
                    os.chown(os.path.join(path, f), 501, 1000)
                for d in dirs:
                    os.chown(os.path.join(path, d), 501, 1000)

            shutil.copy(merlin_file_path + '/merlin.service',
                        mount_path + '/etc/systemd/system/merlin.service')

            subprocess.check_call(['chroot', mount_path,
                                   'systemctl', 'enable', 'merlin'])

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
            shutil.copy(work_dir + '/id_rsa.pub',
                        mount_path + '/home/virtue/.ssh/authorized_keys')
            shutil.copy(work_dir + '/id_rsa.pub',
                        mount_path + '/home/merlin/.ssh/authorized_keys')

            # Install Transducers
            # Copy payload/* to mount_path + '/home/virtue'
            shutil.copy(payload_dir + '/transducer-module.tar.gz',
                        mount_path + '/home/virtue')
            shutil.copy(payload_dir + '/kirk-keystore.jks',
                        mount_path + '/home/virtue')
            shutil.copy(payload_dir + '/truststore.jks',
                        mount_path + '/home/virtue')
            shutil.copy(payload_dir + '/sshd_config',
                        mount_path + '/home/virtue')
            shutil.copy(payload_dir + '/runme.sh', mount_path + '/home/virtue')
            shutil.copy(payload_dir + '/syslog-ng.service',
                        mount_path + '/home/virtue')
            shutil.copy(payload_dir + '/audit.rules',
                        mount_path + '/home/virtue')

            # Create syslog-ng.conf from
            #   payload/syslog-ng-virtue-node.conf.template
            with open(payload_dir + '/syslog-ng-virtue-node.conf.template',
                      'r') as t:
                syslog_ng_config = t.read()
                with open(mount_path + '/home/virtue/syslog-ng.conf', 'w') as f:
                    f.write(syslog_ng_config % (self.elastic_search_node,
                                                self.syslog_server))
            # Create elasticsearch.yml from ELASTIC_YML
            with open(payload_dir + '/elasticsearch.yml.template', 'r') as t:
                elastic_yml = t.read()
                with open(mount_path + '/home/virtue/elasticsearch.yml',
                          'w') as f:
                    f.write(elastic_yml % (self.elastic_search_host))

            # Execute runme.sh with chroot
            os.chmod(mount_path + '/home/virtue/runme.sh', 0775)
            runme_cmd = ['chroot', mount_path, 'bash', '-c',
                         'cd \"/home/virtue\" && ./runme.sh']
            subprocess.check_call(runme_cmd)

            # Install Actuators
            actuator_file_path = os.path.join(payload_dir, 'actuators')
            actuator_files = ['netblock_actuator.deb']
            processkiller_files = ['processkiller.deb']
            files = []
            for f in actuator_files:
                f = os.path.join(actuator_file_path, f)
                #files.append(f)
            for f in processkiller_files:
                f = os.path.join(payload_dir, f)
                files.append(f)

            dpkg_cmd = ['dpkg', '-i', '--force-all', '--root=' + mount_path]
            dpkg_cmd.extend(files)

            subprocess.check_call(dpkg_cmd)

            # Additional actuator config
            '''shutil.copy(mount_path + '/lib/modules/4.13.0-38-generic' +
                        '/updates/dkms/actuator_network.ko',
                        mount_path + '/lib/modules/4.13.0-38-generic' +
                        '/kernel/drivers/')

            with open(mount_path + '/etc/modules', 'a') as modules:
                modules.write('actuator_network\n')'''

            # Additional Process Killer config
            os.chown(mount_path + '/opt/merlin', 501, 1000)
            for path, dirs, files in os.walk(mount_path + '/opt/merlin'):
                for f in files:
                    os.chown(os.path.join(path, f), 501, 1000)
                for d in dirs:
                    os.chown(os.path.join(path, d), 501, 1000)

            subprocess.check_call(['chroot', mount_path,
                                   'systemctl', 'enable', 'processkiller'])

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

    def construct_unity(self, build_options, clean=False):

        WORK_DIR = self.work_dir

        if build_options['env'] == 'aws':
            WORK_DIR = 'keys-unity'
            if not os.path.exists(WORK_DIR):
                os.mkdir(WORK_DIR)

        if os.path.exists(WORK_DIR) and os.listdir(WORK_DIR) != []:
            #is_delete = input("WARNING: working directory '%s' is not empty! Delete? Type 'yes' or 'no':" % (WORK_DIR))
            #if is_delete == 'yes':
            print("Cleaning working directory...")
            shutil.rmtree(WORK_DIR)

        if not os.path.exists(WORK_DIR):
            os.mkdir(WORK_DIR)

        stage_dict = OrderedDict()
        stage_dict[UserStage.NAME] = UserStage(WORK_DIR)
        stage_dict[AptStage.NAME] = AptStage(WORK_DIR)

        if not os.path.exists(WORK_DIR):
            os.makedirs(WORK_DIR)

        for stage in stage_dict:
            if isinstance(stage_dict[stage], CIStage):
                self.run_stage(stage_dict, stage)

        if (build_options['env'] != 'xen'):
            print("All Cloud-Init stages are finished")
            print("Waiting for a VM to come up for ssh stages...")

        vm = None
        instance = ''
        vmname = self.NAME

        if (build_options['env'] == 'qemu'):
            # Deprecated and broken
            self.setup_qemu(build_options, WORK_DIR)
        elif (build_options['env'] == 'aws'):
            # Deprecated
            ssh_data = self.setup_aws(build_options, WORK_DIR, vmname)
            instance = ssh_data[0]
            ssh_host = ssh_data[1]
            ssh_port = ssh_data[2]
        elif (build_options['env'] == 'xen'):
            self.construct_img(build_options, WORK_DIR,
                               os.path.join(os.environ['HOME'],
                                            'galahad',
                                            'assembler',
                                            'payload'))

        if (build_options['env'] != 'xen'):

            stage_dict[KernelStage.NAME] = KernelStage(ssh_host, ssh_port,
                                                       WORK_DIR)
            stage_dict[TransducerStage.NAME] = TransducerStage(
                self.elastic_search_host,
                self.elastic_search_node,
                self.syslog_server,
                ssh_host,
                ssh_port,
                WORK_DIR)
            stage_dict[MerlinStage.NAME] = MerlinStage(ssh_host, ssh_port,
                                                       WORK_DIR)
            stage_dict[ActuatorStage.NAME] = ActuatorStage(ssh_host, ssh_port,
                                                           WORK_DIR)
            stage_dict[ProcessKillerStage.NAME] = ProcessKillerStage(ssh_host,
                                                                     ssh_port,
                                                                     WORK_DIR)

            # We have a shutdown stage to bring the VM down. Of course if you're
            # trying to debug it's worth commenting this out to keep the vm
            # running after the assembly is complete
            stage_dict[ShutdownStage.NAME] = ShutdownStage(ssh_host,
                                                           ssh_port,
                                                           WORK_DIR)

            for stage in stage_dict:
                if isinstance(stage_dict[stage], SSHStage):
                    self.run_stage(stage_dict, stage)#'''

        return_data = ''
        print("Assembler is done")
        if build_options['env'] == 'aws':
            print("Created instance id: %s, name: %s" % (instance, vmname))
            with open(os.path.join(WORK_DIR, "README.md"), 'w') as f:
                f.write('\nInstance ID: %s' % (instance))

            time.sleep(20)

            ami_id = 'NULL'
            private_key = ''
            with open(os.path.join(WORK_DIR, 'id_rsa'), 'r') as rsa:
                private_key = rsa.read()

            if (build_options['create_ami']):
                ec2 = boto3.client('ec2')
                ami_data = ec2.create_image(
                    InstanceId=instance, Name='Unity',
                    Description='Created by assembler on {0}.'.format(
                        build_options['aws_subnet_id']))
                print('AMI data: {0}'.format(ami_data))
                ami_id = ami_data['ImageId']
            return_data = (ami_id, private_key)

        elif (build_options['env'] == 'xen'):

            if (not os.path.exists(build_options['output_dir'])):
                os.makedirs(build_options['output_dir'])

            shutil.copy(os.path.join(WORK_DIR, 'disk.img'),
                        build_options['output_dir'])
            shutil.copy(os.path.join(WORK_DIR, 'id_rsa'),
                        build_options['output_dir'])
            shutil.copy(os.path.join(WORK_DIR, 'id_rsa.pub'),
                        build_options['output_dir'])

        if clean:
            shutil.rmtree(WORK_DIR)

        return return_data

    def assemble_running_vm(self, containers, docker_login,
                            ssh_host, ssh_port='22'):

        docker_stage = DockerVirtueStage(docker_login, containers, ssh_host,
                                         str(ssh_port), self.work_dir,
                                         check_cloudinit=False)

        docker_stage.run()
