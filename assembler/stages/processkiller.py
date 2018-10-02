# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

from assembler.stages.core.ssh_stage import SSHStage
import time
import subprocess, os

class ProcessKillerStage(SSHStage):
    NAME = 'ProcessKillerStage'
    DEPENDS = ['UserStage']

    PAYLOAD_PATH = 'assembler/payload'
    DEB_FILE = 'processkiller.deb'

    def run(self):
        if not self._has_run:
            super(ProcessKillerStage, self).run()
            deb_file_path = os.path.join(self.PAYLOAD_PATH, self.DEB_FILE)
            self._copy_file(deb_file_path, self.DEB_FILE)

            self._exec_cmd('sudo dpkg -i %s' % (self.DEB_FILE))
            self._exec_cmd('sudo chown -R merlin:camelot /opt/merlin')
            self._exec_cmd('sudo systemctl enable processkiller')
            self._exec_cmd('sudo systemctl start processkiller')
            self._exec_cmd('sudo rm %s' % (self.DEB_FILE))
