# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

from assembler.stages.core.ssh_stage import SSHStage

import subprocess, os

class DockerVirtueStage(SSHStage):
    NAME = 'DockerVirtueStage'
    DEPENDS = ['AptStage', 'UserStage']

    USER_SCRIPT = '''#!/bin/bash
        cd /home/virtue
        mkdir %s
        pip3 install --user docker pyyaml
        git clone --branch 283.virtue-sso https://github.com/starlab-io/docker-virtue.git
        cd docker-virtue/virtue
        sudo %s
        sudo ./run.py -p start %s
        cd /home/virtue
        sudo rm -rf docker-virtue
        '''

    def __init__(self, docker_login, containers, ssh_host, ssh_port,
                 work_dir='.', check_cloudinit=True):
        super(DockerVirtueStage, self).__init__(
            ssh_host, ssh_port, work_dir=work_dir,
            check_cloudinit=check_cloudinit)
        self._docker_login = docker_login
        self._containers = containers

    def run(self):
        if not self._has_run:
            super(DockerVirtueStage, self).run()

            # KL
            #self._exec_cmd(self.USER_SCRIPT % (self._docker_login, ' '.join(self._containers)))
            self._exec_cmd(self.USER_SCRIPT % (' '.join(self._containers), self._docker_login,
                                               ' '.join(self._containers)))
