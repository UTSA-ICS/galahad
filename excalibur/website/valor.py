import os
import boto3
import botocore
import rethinkdb

import paramiko
from paramiko import SSHClient

from aws import AWS


class ValorAPI:

    def __init__(self):

        self.rethinkdb_manager = RethinkDbManager()
        self.valor_manager = ValorManager()


    def valor_create(self):

        aws = AWS()
        self.valor_manager.create_valor(
            aws.get_subnet_id(),
            aws.get_sec_group().id)
      
 
    def valor_create_pool(self):
        pass


    def valor_destroy(self):
        pass


    def valor_list(self):
        return self.rethinkdb_manager.list_valors()



class Valor: 

    def __init__(self, subnet, sec_group):

        aws = AWS()

        excalibur_ip = '{0}/32'.format(aws.get_public_ip())
        self.subnet    = subnet
        self.sec_group = sec_group
        self.guestnet  = None

        valor = {
            'image_id' : 'ami-01c5d8354c604b662',
            'inst_type' : 't2.medium',
            'subnet_id' : self.subnet,
            'key_name' : 'starlab-virtue-te',
            'tag_key' : 'Project',
            'tag_value' : 'Virtue',
            'sec_group' : self.sec_group,
            'inst_profile_name' : '',
            'inst_profile_arn' : '', 
        }

        self.aws_instance = aws.instance_create(**valor)

        self.authorize_ssh_connections(excalibur_ip)


    def authorize_ssh_connections(self, ip):

        ec2 = boto3.resource('ec2')
        security_group = ec2.SecurityGroup(self.sec_group)

        #TODO: should the security group already be authorized for SSH?
        try:
            security_group.authorize_ingress(
                CidrIp=ip,
                FromPort=22,
                IpProtocol='tcp',
                ToPort=22 )

        except botocore.exceptions.ClientError:
            print(
                'ClientError encountered while adding sec group rule. '
                + 'Rule may already exist.')


    def get_efs_mount(self):

        stack_name = 'test-for-mvs-1'

        cloudformation = boto3.resource('cloudformation')
        efs_stack = cloudformation.Stack(stack_name)

        for output in efs_stack.outputs:

            if output['OutputKey'] == 'FileSystemID':
                file_system_id = output['OutputValue']

        efs_name = '{}.efs.us-east-1.amazonaws.com'.format(file_system_id)

        return efs_name


    def mount_efs(self):

        efs_mount = self.get_efs_mount()

        make_efs_mount_command = 'sudo mkdir /mnt/efs'

        mount_efs_command = (
            'sudo mount -t nfs '
            '{}:/export '
            '/mnt/efs/').format(efs_mount)

        client = self.connect_with_ssh()

        print(mount_efs_command)
        stdin, stdout, stderr = client.exec_command(make_efs_mount_command)
        stdin, stdout, stderr = client.exec_command(mount_efs_command)

        print('[!] Valor.mount_efs : stdout : ' + stdout.read())
        print('[!] Valor.mount_efs : stderr : ' + stderr.read())


    def connect_with_ssh(self):

        client = SSHClient()

        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:

            client.load_system_host_keys()

            client.connect(
                self.aws_instance.public_ip_address,
                username='ubuntu',
                key_filename=os.environ['HOME'] + '/starlab-virtue-te.pem')

        except:
            print('SSH failed to connect')

        return client


    def setup(self):
        '''
        sudo su
        cp -r /mnt/nfs/deploy-local/compute/config /home/ubuntu/
        cd /home/ubuntu/config && /bin/bash setup.sh
        reboot (redo mounting)
        ovs-vsctl show - see bridge to remote router
        xl list - received:
             `Domain-0                       0  2048     2     r-----     198.6`
        ping 10.91.0.254 - should work
        '''

        self.mount_efs()

        copy_config_directory_command = \
            'sudo cp -r /mnt/nfs/deploy-local/compute/config /home/ubuntu/'

        cd_and_execute_setup_command = \
            'sudo cd /home/ubuntu/config && /bin/bash setup.sh'

        client = self.connect_with_ssh()

        stdin, stdout, stderr = client.exec_command(
            copy_config_directory_command)

        stdin, stdout, stderr = client.exec_command(
            cd_and_execute_setup_command)


    def launch_virtue(self, id, virtue_path):

        # Write to rethink
        rdb = RethinkDbManager()
        rdb.add_virtue(self.aws_instance.id, id, virtue_path)


    def wait_until_accessible(self):

        max_attempts = 10

        for attempt_number in range(max_attempts):

            try:

                self.connect_with_ssh()
                print('Successfully connected to {}'.format(self.aws_instance.public_ip_address,))

                break

            except Exception as e:
                print(e)
                print('Attempt {0} failed to connect').format(attempt_number+1)


class ValorManager:

    def __init__(self):

        self.rethinkdb_manager = RethinkDbManager()
        self.router_manager = RouterManager()


    def get_empty_valor(self):
        pass


    def create_valor(self, subnet, sec_group):

        valor = Valor(subnet, sec_group)

        valor.wait_until_accessible()

        self.rethinkdb_manager.add_valor(valor)

        self.router_manager.add_valor(valor)

        valor.setup()


    def create_valor_pool(self, number_of_valors):
        pass


class RethinkDbManager:

    ip_address = '172.30.1.54'

    def __init__(self):
        self.connection = rethinkdb.connect(self.ip_address, 28015).repl()


    def list_valors(self):

        response = rethinkdb.db('routing').table('galahad').run()

        valors = list(response.items)

        return valors


    def add_valor(self, valor):

        assert valor.guestnet == None

        # TODO: We need to use new guestnet for each valor
        record = {
            'function': 'valor',
            'guestnet': '10.91.0.1',
            'host'    : valor.aws_instance.id,
            'address' : valor.aws_instance.private_ip_address
        }

        rethinkdb.db('routing').table('galahad').insert([record]).run()
        valor.guestnet = record['guestnet']


    def add_virtue(self, valor_hostname, virtue_hostname, efs_path):

        # TODO: How do we decide what address and guestnet to use?
        record = {
            'function': 'virtue',
            'host'    : virtue_hostname,
            'valor'   : valor_hostname,
            'guestnet': '10.91.0.5',
            'img_path': efs_path
        }

        self.client.db('routing').table('galahad').insert([record]).run()


class RouterManager:

    ip_address = ''

    def add_valor(self, valor):
        pass
