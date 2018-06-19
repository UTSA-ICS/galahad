import subprocess
import boto3


class ssh_tool():
    def __init__(self, username, ip_address, sshkey=None):
        self.rem_username = username
        self.ip = ip_address
        self.sshkey = sshkey

    def ssh(self, command, test=True):

        if (self.sshkey == None):
            keyls = []
        else:
            keyls = ['-i', self.sshkey]

        call_list = ['ssh'] + keyls + [
            '-o', 'StrictHostKeyChecking=no',
            self.rem_username + '@' + self.ip, command
        ]

        print
        print
        print
        "{0}  {1}".format(self.ip, command)
        print
        ' '.join(call_list)
        print

        ret = subprocess.call(call_list)

        # By default, it is not ok to fail
        if (test):
            assert ret == 0

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
        print
        print
        "{0}  {1}  {2}".format(self.ip, file_path_local, file_path_remote)
        print
        ' '.join(call_list)
        print

        ret = subprocess.call(call_list)

        # By default, it is not ok to fail
        if (test):
            assert ret == 0

        return ret


def get_excalibur_server_ip(stack_name):
    client = boto3.client('ec2')
    server = client.describe_instances(
        Filters=[{
            'Name': 'tag:aws:cloudformation:logical-id',
            'Values': ['ExcaliburServer']
        }, {
            'Name': 'tag:aws:cloudformation:stack-name',
            'Values': [stack_name]
        }, {
            'Name': 'instance-state-name',
            'Values': ['running']
        }])
    # Return public IP
    return server['Reservations'][0]['Instances'][0]['PublicIpAddress']
