# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

from assembler.stages.core.ssh_stage import SSHStage

import subprocess, os

class DockerVirtueStage(SSHStage):
    NAME = 'DockerVirtueStage'
    DEPENDS = ['AptStage', 'UserStage']

    USER_SCRIPT = '''#!/bin/bash
        cd /home/virtue
        pip3 install --user docker
        git clone https://github.com/starlab-io/docker-virtue.git
        cd docker-virtue/virtue
        sudo %s
        sudo ./run.py -pr start %s
        cd /home/virtue
        sudo rm -rf docker-virtue
        '''

    def __init__(self, docker_login, containers, ssh_host, ssh_port, work_dir='.'):
        super(DockerVirtueStage, self).__init__(ssh_host, ssh_port, work_dir=work_dir)
        self._docker_login = docker_login
        self._containers = containers

    def run(self):
        if not self._has_run:
            super(DockerVirtueStage, self).run()

            self._exec_cmd(self.USER_SCRIPT % (self._docker_login, ' '.join(self._containers)))
