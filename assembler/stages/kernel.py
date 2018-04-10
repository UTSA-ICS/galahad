from stages.core.ssh_stage import SSHStage

import subprocess, os

class KernelStage(SSHStage):
    ''' This stage is a demo stage for how to use SSHStage tools '''
    NAME = 'KernelStage'
    DEPENDS = ['UserStage']

    def run(self):
        if not self._has_run:
            super().run()
            deb_file_path = os.path.join('..', 'unity', 'latest-debs')
            files = ['linux-headers-4.13.0-36_4.13.0-36.40+unity1_all.deb', 'linux-image-4.13.0-36-generic_4.13.0-36.40+unity1_amd64.deb']
            for f in files:
                self._copy_file(os.path.join(deb_file_path, f), f)
            self._exec_cmd('sudo dpkg -i --force-all '+' '.join(files))
