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

    SYSTEMCTL_UNIT = '''[Unit]
After=network.target

[Service]
Type=forking
ExecStart=/etc/init.d/merlin start

[Install]
WantedBy=multi-user.target
'''

    def run(self):
        if not self._has_run:
            super().run()
            deb_file_path = os.path.join(self.PAYLOAD_PATH, self.DEB_FILE)
            systemctl_vmpath = '/etc/systemd/system/merlin.service'
            systemctl_filename = os.path.basename(systemctl_vmpath)
            systemctl_path = os.path.join(self._work_dir, systemctl_filename)

            with open(systemctl_path, 'w') as f:
                f.write(self.SYSTEMCTL_UNIT)
            self._copy_file(systemctl_path, systemctl_filename)
            self._copy_file(deb_file_path, self.DEB_FILE)

            self._exec_cmd('sudo dpkg -i %s' % (self.DEB_FILE))
            self._exec_cmd('sudo chown -R merlin:camelot /opt/merlin')
            self._exec_cmd('sudo chmod 777 /opt/merlin')
            self._exec_cmd('sudo chown -R merlin:camelot /var/private/ssl')
            self._exec_cmd('sudo mv %s %s' % (systemctl_filename, systemctl_vmpath))
            self._exec_cmd('sudo systemctl enable merlin')
            self._exec_cmd('sudo systemctl start merlin')
            self._exec_cmd('sudo rm merlin.deb')
