# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

from stages.core.ssh_stage import SSHStage
import time
import subprocess, os

class ActuatorStage(SSHStage):
    ''' This stage is a demo stage for how to use SSHStage tools '''
    NAME = 'ActuatorStage'
    DEPENDS = ['UserStage', 'DockerVirtueStage', 'MerlinStage', 'TransducerInstallStage', 'KernelStage']

    def run(self):
        if not self._has_run:
            super().run()
            actuator_file_path = os.path.join('payload', 'actuators')
            files = ['netblock_actuator.deb']
            for f in files:
                self._copy_file(os.path.join(actuator_file_path, f), f)
                self._exec_cmd_with_retry('sudo dpkg -i ' + f)
            for f in files:
                self._exec_cmd_with_retry('rm %s' % (f))
            self._exec_cmd_with_retry('sudo insmod /lib/modules/4.13.0-38-generic/updates/dkms/actuator_network.ko')
            self._exec_cmd_with_retry('sudo chown merlin:merlin /dev/netblockchar')
            self._exec_cmd_with_retry('echo "/lib/modules/4.13.0-38-generic/updates/dkms/actuator_network.ko" | sudo tee -a /etc/modules')
