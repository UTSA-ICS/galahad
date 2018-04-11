from stages.core.ci_stage import CIStage

import subprocess, os

class AptStage(CIStage):
    NAME = 'AptStage'
    DEPENDS = []

    def run(self):
        if not self._has_run:
            super().run()
            self._ci.install_package('docker.io')
            self._ci.install_package('git')
            self._ci.install_package('python3')
            self._ci.install_package('python3-pip')
            self._ci.install_package('python')
            self._ci.install_package('python-pip')
            self._ci.save(self._work_dir)
