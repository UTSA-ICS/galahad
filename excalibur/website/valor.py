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

    def __init__(self, valor_id):

        self.valor = self.ec2.Instance(valor_id)
        self.guestnet = None


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

        stack_name = 'test-for-mvs-2'

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

        mount_efs_command = 'sudo mount -t nfs {}:/ /mnt/efs'.format(efs_mount)

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

        except Exception as error:

            print(error)
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
            'sudo cp -r /mnt/efs/deploy/compute/config /home/ubuntu/'

        cd_and_execute_setup_command = \
            'cd /home/ubuntu/config && sudo /bin/bash setup.sh'

        client = self.connect_with_ssh()

        stdin, stdout, stderr = client.exec_command(
            copy_config_directory_command)
        print('[!] copy_config_dir : stdout : ' + stdout.read())
        print('[!] copy_config_dir : stderr : ' + stderr.read())

        stdin, stdout, stderr = client.exec_command(
            cd_and_execute_setup_command)
        print('[!] execute_setup : stdout : ' + stdout.read())
        print('[!] execute_setup : stderr : ' + stderr.read())


    def wait_until_accessible(self):

        max_attempts = 10

        for attempt_number in range(max_attempts):

            try:

                self.connect_with_ssh()
                print('Successfully connected to {}'.format(
                    self.aws_instance.public_ip_address,))

                break

            except Exception as error:
                print(error)
                print('Attempt {0} failed to connect').format(attempt_number+1)


class ValorManager:

    def __init__(self):

        self.rethinkdb_manager = RethinkDbManager()
        self.router_manager = RouterManager()


    def get_empty_valor(self):
        pass


    def create_valor(self, subnet, sec_group):

        aws = AWS()

        excalibur_ip = '{0}/32'.format(aws.get_public_ip())

        valor = {
            'image_id' : 'ami-01c5d8354c604b662',
            'inst_type' : 't2.medium',
            'subnet_id' : subnet,
            'key_name' : 'starlab-virtue-te',
            'tag_key' : 'Project',
            'tag_value' : 'Virtue',
            'sec_group' : sec_group,
            'inst_profile_name' : '',
            'inst_profile_arn' : '',
        }

        instance = aws.instance_create(**valor)

        valor = Valor(instance.id)

        valor.authorize_ssh_connections(excalibur_ip)

        valor.wait_until_accessible()

        self.rethinkdb_manager.add_valor(valor)

        self.router_manager.add_valor(valor)

        valor.setup()


    def create_valor_pool(self, number_of_valors):
        pass


    def destroy_valor(self, valor_id):

        aws = AWS()

        aws.instance_destroy(valor_id, block=False)




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


    def get_free_guestnet(self):

        guestnet = '10.91.0.{0}'

        for test_number in range(1, 256):
            results = rethinkdb.db('routing').table('galahad').filter({
                'guestnet': guestnet.format(test_number)
            }).run()
            if (len(list(results)) == 0):
                guestnet = guestnet.format(test_number)
                break

        # If this fails, then there was no available guestnet
        assert '{0}' not in guestnet

        return guestnet


    def add_virtue(self, valor_address, virtue_hostname, efs_path):

        matching_virtues = list(rethinkdb.db('routing').table('galahad').filter({
            'function': 'virtue',
            'host': virtue_hostname
        }).run())

        assert len(matching_virtues) == 0

        guestnet = self.get_free_guestnet()

        record = {
            'function': 'virtue',
            'host'    : virtue_hostname,
            'address' : valor_address,
            'guestnet': guestnet,
            'img_path': efs_path
        }

        rethinkdb.db('routing').table('galahad').insert([record]).run()


    def get_virtue(self, virtue_hostname):

        matching_virtues = list(rethinkdb.db('routing').table('galahad').filter({
            'function': 'virtue',
            'host': virtue_hostname
        }).run())

        if (len(matching_virtues) != 1):
            return matching_virtues

        return matching_virtues[0]


    def remove_virtue(self, virtue_hostname):

        matching_virtues = list(rethinkdb.db('routing').table('galahad').filter({
            'function': 'virtue',
            'host': virtue_hostname
        }).run())

        assert len(matching_virtues) == 1

        rethinkdb.db('routing').table('galahad').filter(matching_virtues[0]).delete().run()


class RouterManager:

    ip_address = ''

    def add_valor(self, valor):
        pass
