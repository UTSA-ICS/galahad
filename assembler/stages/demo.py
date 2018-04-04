from stages.core.ssh_stage import SSHStage

import subprocess, os

class DemoStage(SSHStage):
    ''' This stage is a demo stage for how to use SSHStage tools '''
    NAME = 'DemoStage'
    DEPENDS = ['UserStage']

    def run(self):
        if not self._has_run:
            super().run()
            demo_file_path = os.path.join(self._work_dir, 'demo.txt')
            with open(demo_file_path, 'w') as f:
                f.write("I am a file passed over scp\n")
            self._copy_file(demo_file_path, 'demo.txt')
            self._exec_cmd('cat demo.txt')
