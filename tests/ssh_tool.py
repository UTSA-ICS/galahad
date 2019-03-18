import subprocess
import time


class ssh_tool():
    def __init__(self, username, ip_address, sshkey=None):
        self.rem_username = username
        self.ip = ip_address
        self.sshkey = sshkey

    def ssh(self, command, test=True, option=None, output=False):

        if (self.sshkey == None):
            keyls = []
        else:
            keyls = ['-i', self.sshkey]

        if option == None:
            call_list = ['ssh'] + keyls + [
                '-o', 'StrictHostKeyChecking=no',
                self.rem_username + '@' + self.ip, command
            ]
        else:
            call_list = ['ssh'] + keyls + [
                '-o', 'StrictHostKeyChecking=no',
                '-o', option,
                self.rem_username + '@' + self.ip, command
            ]

        print('ssh_tool: ' + ' '.join(call_list))

        stdout = ''
        ret = -1
        if output:
            try:
                stdout = subprocess.check_output(call_list, stderr=subprocess.STDOUT)
                ret = 0
            except subprocess.CalledProcessError as e:
                ret = e.returncode
                print e
                print stdout
        else:
            ret = subprocess.call(call_list)

        if ret != 0:
            print stdout

        # By default, it is not ok to fail
        if (test):
            assert ret == 0

        if output:
            return stdout
        else:
            return ret

    def scp_to(self, file_path_local, file_path_remote='', test=True):

        if (self.sshkey == None):
            keyls = []
        else:
            keyls = ['-i', self.sshkey]

        call_list = ['scp', '-r'] + keyls + [
            file_path_local,
            self.rem_username + '@' + self.ip + ':' + file_path_remote
        ]

        print('ssh_tool: ' + ' '.join(call_list))

        ret = subprocess.call(call_list)

        # By default, it is not ok to fail
        if (test):
            assert ret == 0

        return ret

    def check_access(self):
        # Check if the machine is accessible:
        for i in range(10):
            out = self.ssh('uname -a', test=False)
            if out == 255:
                time.sleep(30)
            else:
                print('Successfully connected to {}'.format(self.ip))
                return True
        return False

    def scp_from(self, file_path_local, file_path_remote='', test=True):

        if (self.sshkey == None):
            keyls = []
        else:
            keyls = ['-i', self.sshkey]

        call_list = ['scp', '-r'] + keyls + [
            self.rem_username + '@' + self.ip + ':' + file_path_remote,
            file_path_local
        ]

        print('ssh_tool: ' + ' '.join(call_list))

        ret = subprocess.call(call_list)

        # By default, it is not ok to fail
        if (test):
            assert ret == 0

        return ret
