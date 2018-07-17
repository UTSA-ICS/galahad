import os, sys, shutil
import json, time
import subprocess
from urlparse import urlparse
import boto3

from stages.core.ci_stage import CIStage
from stages.core.ssh_stage import SSHStage

from stages.kernel import KernelStage
from stages.shutdown import ShutdownStage
from stages.user import UserStage
from stages.apt import AptStage
from stages.virtued import DockerVirtueStage
from stages.transducer_install import TransducerStage
from stages.merlin import MerlinStage

class Assembler():

    WORK_DIR = 'tmp/' # where all the generated files will live
    ISO_FILE = 'virtue.cloudinit.iso'
    LOG_FILE = 'SERIAL.log'

    NAME = ''

    def __init__(self,
                 build_options,
                 docker_login,
                 es_node='https://172.30.128.129:9200',
                 syslog_server='172.30.128.131',
                 rethinkdb_host='172.30.128.130'):
        self.build_options = build_options
        self.docker_login = docker_login
        self.elastic_search_node = es_node
        self.elastic_search_host = urlparse(es_node).hostname
        self.syslog_server = syslog_server
        self.rethinkdb_host = rethinkdb_host

    def start_aws_vm(self, image_id, instance_type, sec_group,
                     subnet, userdata, name, disk_size):
        print("Starting VM, %s" % (name))

        ec2 = boto3.resource('ec2')

        output = ec2.create_instances(
            ImageId=image_id,
            InstanceType=instance_type,
            MinCount=1,
            MaxCount=1,
            Monitoring={'Enabled': False},
            SecurityGroupIds=[sec_group],
            SubnetId=subnet,
            UserData=userdata,)
        '''    BlockDeviceMappings=[{
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
            ])'''

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


    def assemble_role(self, containers, clean=True):

        WORK_DIR = self.WORK_DIR

        if self.build_options['env'] == 'aws':
            WORK_DIR = 'keys-%s' % ('-'.join(containers))
            if not os.path.exists(WORK_DIR):
                os.mkdir(WORK_DIR)

        if os.listdir(WORK_DIR) != []:
            #is_delete = input("WARNING: working directory '%s' is not empty! Delete? Type 'yes' or 'no':" % (WORK_DIR))
            #if is_delete == 'yes':
            print("Cleaning working directory...")
            shutil.rmtree(WORK_DIR)
            os.mkdir(WORK_DIR)


        stage_dict = {}
        stage_dict[UserStage.NAME] = UserStage(WORK_DIR)
        stage_dict[AptStage.NAME] = AptStage(WORK_DIR)

        if not os.path.exists(WORK_DIR):
            os.makedirs(WORK_DIR)

        for stage in stage_dict:
            if isinstance(stage_dict[stage], CIStage):
                self.run_stage(stage_dict, stage)

        print("All Cloud-Init stages are finished")
        print("Waiting for a VM to come up for ssh stages...")

        vm = None
        instance = ''
        vmname = self.NAME

        if self.build_options['env'] == 'qemu':
            if args.resize_img:
                # figure out image size by parsing output of 'qemu-img info $IMAGE'
                qemu_img = subprocess.Popen(['qemu-img', 'info', args.start_vm], stdout=subprocess.PIPE)
                qemu_img.wait()
                img_size = int(re.search('\(([0-9]+) bytes\)', str(qemu_img.stdout.read())).group(1))
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

        elif (self.build_options['env'] == 'aws'):
            #args.ssh_host = input("SSH host: ")
            #args.ssh_port = input("SSH port: ")
            '''Potentially can start AWS instance here instead. To launch new instance in starlab's environment last time this worked:
            aws ec2 run-instances --image-id ami-43a15f3e --count 1 --instance-type t2.micro --security-group-ids sg-0676d24f --subnet-id subnet-0b97b651 --iam-instance-profile "Name=Virtue-Tester" --user-data "$(cat tmp/user-data)" --tag-specifications "ResourceType=instance,Tags=[{Key=Project,Value=Virtue},{Key=Name,Value=BBN-Assembler}]"


            you can then get its IP address with

            aws ec2 describe-instances --instance-ids i-032d5f28b9281e42d --query "Reservations[*].Instances[*].PublicIpAddress"

            But somehow wrong tmp/user-data often ends up in the VM.

            Uploading user-data through a web-browser seems to also not work sometimes (maybe caching?)
            '''
            if vmname == '':
                vmname = 'Unity-%s' % ('-'.join(containers))
            with open(os.path.join(WORK_DIR, 'user-data'), 'r') as f:
                # Todo: Get aws_image_id by finding unity image
                instance = self.start_aws_vm(
                    self.build_options['aws_image_id'],
                    self.build_options['aws_instance_type'],
                    self.build_options['aws_security_group'],
                    self.build_options['aws_subnet_id'],
                    f.read(),
                    vmname,
                    self.build_options['aws_disk_size'])
                print("New instance id: %s" % (instance))
                #return
                ssh_host = self.get_vm_ip(instance)
                print("New instance ip: %s" % (ssh_host))
                ssh_port = '22'
            print("Waiting for VM to start...")
            time.sleep(10)

        stage_dict[DockerVirtueStage.NAME] = DockerVirtueStage(
            self.docker_login,
            containers,
            ssh_host,
            ssh_port,
            WORK_DIR)
        stage_dict[KernelStage.NAME] = KernelStage(ssh_host, ssh_port, WORK_DIR)
        stage_dict[TransducerStage.NAME] = TransducerStage(
            self.elastic_search_host,
            self.elastic_search_node,
            self.syslog_server,
            ssh_host,
            ssh_port,
            WORK_DIR)
        stage_dict[MerlinStage.NAME] = MerlinStage(ssh_host, ssh_port, WORK_DIR)

        # We have a shutdown stage to bring the VM down. Of course if you're trying to debug it's
        # worth commenting this out to keep the vm running after the assembly is complete
        #stage_dict[ShutdownStage.NAME] = ShutdownStage(args.ssh_host, args.ssh_port, WORK_DIR)

        for stage in stage_dict:
            if isinstance(stage_dict[stage], SSHStage):
                self.run_stage(stage_dict, stage)

        print("Assembler is done")
        if self.build_options['env'] == 'aws':
            print("Created instance id: %s, name: %s" % (instance, vmname))
            with open(os.path.join(WORK_DIR, "README.md"), 'w') as f:
                for c in containers:
                    f.write(' - %s\n' % (c))
                f.write('\nInstance ID: %s' % (instance))

            time.sleep(20)

            ami_id = 'NULL'
            private_key = ''
            with open(os.path.join(WORK_DIR, 'id_rsa'), 'r') as rsa:
                private_key = rsa.read()

            if (self.build_options['create_ami']):
                ec2 = boto3.client('ec2')
                ami_data = ec2.create_image(
                    InstanceId=instance, Name='Virtue-'+'-'.join(containers),
                    Description='Created by assembler on {0}.'.format(
                        self.build_options['aws_subnet_id']))
                print('AMI data: {0}'.format(ami_data))
                ami_id = ami_data['ImageId']
            return_data = (ami_id, private_key)

        if clean:
            shutil.rmtree(WORK_DIR)

        return return_data
