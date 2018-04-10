from stages.core.ci_stage import CIStage

import subprocess, os

class UserStage(CIStage):
    ''' This stage creates cloud-init config to create user 'virtue' with a new key pair '''
    NAME = 'UserStage'
    DEPENDS = []

    def run(self):
        if not self._has_run:
            super().run()
            key_file = os.path.join(self._work_dir, 'id_rsa')
            subprocess.check_call(['ssh-keygen', '-N', '', '-f', key_file])
            key = ''
            with open('%s.pub' % (key_file), 'r') as f:
                key = f.read()
            self._ci.add_user('virtue', ssh_authorized_keys=key)
            self._ci.save(self._work_dir)