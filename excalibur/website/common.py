import subprocess
import boto3


class ssh_tool():
    def __init__(self, username, ip_address, sshkey=None):
        self.rem_username = username
        self.ip = ip_address
        self.sshkey = sshkey

    def ssh(self, command, test=True, option=None):

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

        print
        print("{0}  {1}".format(self.ip, command))
        #print(' '.join(call_list))

        ret = subprocess.call(call_list)

        # By default, it is not ok to fail
        #if (test):
        #    assert ret == 0

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

        print
        print("{0}  {1}  {2}".format(self.ip, file_path_local, file_path_remote))
        #print(' '.join(call_list))

        ret = subprocess.call(call_list)

        # By default, it is not ok to fail
        if (test):
            assert ret == 0

        return ret
