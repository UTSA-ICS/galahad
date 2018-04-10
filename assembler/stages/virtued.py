from stages.core.ssh_stage import SSHStage

import subprocess, os

class DockerVirtueStage(SSHStage):
    NAME = 'DockerVirtueStage'
    DEPENDS = ['AptStage', 'UserStage', 'KernelStage']

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

    def run(self):
        if not self._has_run:
            super().run()

            self._exec_cmd(self.USER_SCRIPT % (self._args.docker_login, ' '.join(self._args.containers)))
