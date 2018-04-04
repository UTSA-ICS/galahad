#!/usr/bin/env python3 

import argparse, os, subprocess, sys, re

from stages.user import UserStage
from stages.apt import AptStage
from stages.virtued import DockerVirtueStage
from stages.core.ci_stage import CIStage
from stages.core.ssh_stage import SSHStage

from stages.demo import DemoStage
from stages.shutdown import ShutdownStage

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
    parser.add_argument('--docker-login', help='docker login command as given by the aws cli')
    parser.add_argument('-i', '--start-vm', metavar='IMAGE', help='Start qemu-kvm on IMAGE and apply generated cloud-init to it')
    parser.add_argument('-s', '--ssh-host', default='127.0.0.1', help='SSH hostname for SSH stages. Default 127.0.0.1')
    parser.add_argument('-p', '--ssh-port', default='5555', help='SSH port for SSH stages. Default 5555')
    parser.add_argument('-r', '--resize-img', metavar='MOD.SIZE', default='+3g', help='Call `qemu-img resize $IMAGE MOD.SIZE`')
    parser.add_argument('-c', '--clean', action='store_true', help='Clean the working directory when done')
    parser.add_argument('containers', nargs='*', help='Docker container names that docker-virtue repository supports')
    args = parser.parse_args()



    stage_dict = {}
    stage_dict[UserStage.NAME] = UserStage(args, WORK_DIR)
    stage_dict[AptStage.NAME] = AptStage(args, WORK_DIR)
    stage_dict[DockerVirtueStage.NAME] = DockerVirtueStage(args, WORK_DIR)
    stage_dict[DemoStage.NAME] = DemoStage(args, WORK_DIR)
    # We have a shutdown stage to bring the VM down. Of course if you're trying to debug it's 
    # worth commenting this out to keep the vm running after the assembly is complete
    #stage_dict[ShutdownStage.NAME] = ShutdownStage(args, WORK_DIR)

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

    for stage in stage_dict:
        if isinstance(stage_dict[stage], SSHStage):
            run_stage(stage_dict, stage)

    print("Assembler is done")

