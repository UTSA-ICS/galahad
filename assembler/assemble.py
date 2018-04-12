#!/usr/bin/env python3 

import argparse, os, subprocess, sys, re, shutil, json

from stages.core.ci_stage import CIStage
from stages.core.ssh_stage import SSHStage

from stages.kernel import KernelStage
from stages.shutdown import ShutdownStage
from stages.user import UserStage
from stages.apt import AptStage
from stages.virtued import DockerVirtueStage
from stages.transducer_install import TransducerStage
from stages.merlin import MerlinStage

WORK_DIR = 'tmp/' # where all the generated files will live
ISO_FILE = 'virtue.cloudinit.iso'
LOG_FILE = 'SERIAL.log'

def run_stage(stages, stage):
    for dep in stages[stage].DEPENDS:
        if dep not in stages.keys():
            raise ValueError("Stage %s depends on undefined stage %s" % (stage, dep))
        run_stage(stages, dep)
    stages[stage].run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Assemble virtue components into a VM')
    parser.add_argument('--docker-login', required=True, help='docker login command as given by the aws cli')
    parser.add_argument('--elastic-search-node', default='https://172.30.128.129:9200', help='http(s) url of your elasticsearch cluster. Goes into syslog module.')
    parser.add_argument('--syslog-server', default='172.30.128.131', help='ip/hostname of the syslog server, goes into syslog module.')
    parser.add_argument('--elastic-search-host', default='172.30.128.129', help='ip/hostname of elastic search node (not sure if used but needs to not be empty)')
    parser.add_argument('--rethinkdb-host', default='172.30.128.130', help='ip/hostname of the RethinkDB that goes into merlin')
    parser.add_argument('-i', '--start-vm', metavar='IMAGE', help='Start qemu-kvm on IMAGE and apply generated cloud-init to it')
    parser.add_argument('-s', '--ssh-host', default='127.0.0.1', help='SSH hostname for SSH stages. Default 127.0.0.1')
    parser.add_argument('-p', '--ssh-port', default='5555', help='SSH port for SSH stages. Default 5555')
    parser.add_argument('-r', '--resize-img', metavar='MOD.SIZE', default='+3g', help='Call `qemu-img resize $IMAGE MOD.SIZE`')
    parser.add_argument('-c', '--clean', action='store_true', help='Clean the working directory when done. WARNING! This will delete the generated RSA Keys')
    parser.add_argument('containers', nargs='*', help='Docker container names that docker-virtue repository supports')
    args = parser.parse_args()



    stage_dict = {}
    stage_dict[UserStage.NAME] = UserStage(args, WORK_DIR)
    stage_dict[AptStage.NAME] = AptStage(args, WORK_DIR)
    stage_dict[DockerVirtueStage.NAME] = DockerVirtueStage(args, WORK_DIR)
    stage_dict[KernelStage.NAME] = KernelStage(args, WORK_DIR)
    stage_dict[TransducerStage.NAME] = TransducerStage(args, WORK_DIR)
    stage_dict[MerlinStage.NAME] = MerlinStage(args, WORK_DIR)

    # We have a shutdown stage to bring the VM down. Of course if you're trying to debug it's 
    # worth commenting this out to keep the vm running after the assembly is complete
    #stage_dict[ShutdownStage.NAME] = ShutdownStage(args, WORK_DIR)
    
    if not os.path.exists(WORK_DIR):
        os.makedirs(WORK_DIR)

    for stage in stage_dict:
        if isinstance(stage_dict[stage], CIStage):
            run_stage(stage_dict, stage)

    print("All Cloud-Init stages are finished")
    print("Waiting for a VM to come up for ssh stages...")
    
    vm = None

    if args.start_vm:
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

    else:
        args.ssh_host = input("SSH host: ")
        args.ssh_port = input("SSH port: ")
        '''Potentially can start AWS instance here instead. To launch new instance in starlab's environment last time this worked:
        aws ec2 run-instances --image-id ami-43a15f3e --count 1 --instance-type t2.micro --security-group-ids sg-0676d24f --subnet-id subnet-0b97b651 --iam-instance-profile "Name=Virtue-Tester" --user-data "$(cat tmp/user-data)" --tag-specifications "ResourceType=instance,Tags=[{Key=Project,Value=Virtue},{Key=Name,Value=BBN-Assembler}]"


        you can then get its IP address with

        aws ec2 describe-instances --instance-ids i-032d5f28b9281e42d --query "Reservations[*].Instances[*].PublicIpAddress"

        But somehoe wrong tmp/user-data often ends up in the VM.

        Uploading user-data through a web-browser seems to also not work sometimes (maybe caching?)
        '''

    for stage in stage_dict:
        if isinstance(stage_dict[stage], SSHStage):
            run_stage(stage_dict, stage)

    if args.clean:
        shutil.rmtree(WORK_DIR)

    print("Assembler is done")

