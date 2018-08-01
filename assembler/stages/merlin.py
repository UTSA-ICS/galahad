# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

from stages.core.ssh_stage import SSHStage
import time
import subprocess, os

class MerlinStage(SSHStage):
    ''' This stage is a demo stage for how to use SSHStage tools '''
    NAME = 'MerlinStage'
    DEPENDS = ['UserStage', 'DockerVirtueStage']

    PAYLOAD_PATH = 'payload'
    DEB_FILE = 'merlin.deb'

    def run(self):
        if not self._has_run:
            super().run()
            deb_file_path = os.path.join(self.PAYLOAD_PATH, self.DEB_FILE)
            self._copy_file(deb_file_path, self.DEB_FILE)

            self._exec_cmd('sudo dpkg -i %s' % (self.DEB_FILE))
            self._exec_cmd('sudo chown -R merlin:camelot /opt/merlin')
            self._exec_cmd('sudo chmod 777 /opt/merlin')
            self._exec_cmd('sudo chown -R merlin:camelot /var/private/ssl')
            self._exec_cmd('sudo systemctl enable merlin')
            self._exec_cmd('sudo systemctl start merlin')
            self._exec_cmd('sudo rm merlin.deb')
