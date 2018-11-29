# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

import tempfile, subprocess, os
from time import sleep

class SSHStage(object):
    NAME = 'CoreSSH'
    DEPENDS = ['UserStage']

    def __init__(self, ssh_host, ssh_port, work_dir='.', check_cloudinit=True):
        self._ssh_host = ssh_host
        self._ssh_port = ssh_port
        self._work_dir = work_dir
        self._check_cloudinit = check_cloudinit
        self._has_run = False
        self._is_up = False
        self._cloudinit_is_done = not check_cloudinit

    def _wait_for_host_is_up(self):
        # Timeout after 5 min - Virtue is unreachable.
        timeout = 360
        elapsed_time = 0
        while not self._is_up:
            if elapsed_time >= timeout:
                raise Exception('Failed to connect to Virtue within {} seconds'.format(timeout))
            try:
                self._exec_cmd('echo hi')
                self._is_up = True
            except subprocess.CalledProcessError:
                self._is_up = False
                sleep(5)
                elapsed_time = elapsed_time + 5

    def _wait_for_cloudinit_is_done(self):
        self._cloudinit_is_done = not self._check_cloudinit
        while not self._cloudinit_is_done:
            try:
                self._exec_cmd('grep -E "Cloud-init .+ finished" /var/log/cloud-init.log')
                self._cloudinit_is_done = True
            except subprocess.CalledProcessError as e:
                if e.returncode == 1: # grep didn't match regex
                    print("Waiting for cloud-init to finish setup...")
                    self._cloudinit_is_done = False
                    sleep(5)
                elif e.returncode == 255:
                    print("Endpoint is unreachable, trying again shortly...")
                    self._cloudinit_is_done = False
                    sleep(5)
                else:
                    raise e

    def _exec_cmd(self, cmd):
        self._ssh_cmd_is_done = False
        ssh = ['ssh', '-i', os.path.join(self._work_dir, 'id_rsa'), '-p', str(self._ssh_port), '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', 'virtue@%s' % (self._ssh_host)]
        if type(cmd) is list:
            ssh.extend(cmd)
        else:
            ssh.append(cmd)
        print(' '.join(ssh))
        subprocess.check_call(ssh)


    def _exec_cmd_with_retry(self, cmd):
        self._ssh_cmd_is_done = False
        ssh = ['ssh', '-i', os.path.join(self._work_dir, 'id_rsa'), '-p', str(self._ssh_port), '-o',
               'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', 'virtue@%s' % (self._ssh_host)]
        if type(cmd) is list:
            ssh.extend(cmd)
        else:
            ssh.append(cmd)
        print(' '.join(ssh))
        # It seems like, occasionally, ssh connections will be unavailable for a small amount of time
        # Adding retrys to try and mitigate this crashing the asemmbly
        while not self._ssh_cmd_is_done:
            try:
                subprocess.check_call(ssh)
                self._ssh_cmd_is_done = True
            except subprocess.CalledProcessError as e:
                if e.returncode == 255:
                    self._ssh_cmd_is_done = False
                    print("Endpoint is unreachable, trying again shortly...")
                    sleep(5)
                else:
                    raise e


    def _copy_file(self, local_source_path, remote_destination_path):
        scp = ['scp', '-i', os.path.join(self._work_dir, 'id_rsa'), '-P', str(self._ssh_port), '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', local_source_path, 'virtue@%s:%s' % (self._ssh_host, remote_destination_path)]
        print(' '.join(scp))
        subprocess.check_call(scp)

    def run(self):
        if not self._has_run:
            print("Running %s stage" % (self.NAME))
            self._wait_for_host_is_up()
            self._wait_for_cloudinit_is_done()
            self._has_run = True
