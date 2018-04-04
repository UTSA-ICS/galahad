from stages.core.ci_stage import CIStage

import subprocess, os

class DockerVirtueStage(CIStage):
    NAME = 'DockerVirtueStage'
    DEPENDS = ['AptStage', 'UserStage']

    USER_SCRIPT = '''#!/bin/bash
        pip3 install docker
        cd /home/virtue
        su - virtue
        git clone https://github.com/starlab-io/docker-virtue.git
        cd docker-virtue/virtue
        %s
        ./run.py -p start %s'''

    def run(self):
        if not self._has_run:
            super().run()

            self._ci.run_cmd(self.USER_SCRIPT % (self._args.docker_login, ' '.join(self._args.containers)))
            self._ci.save(self._work_dir)
