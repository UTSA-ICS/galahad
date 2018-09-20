import boto3
import botocore
import os
import paramiko
import rethinkdb
import time

from paramiko import SSHClient
from aws import AWS


class ValorAPI:

    def __init__(self):

        self.rethinkdb_manager = RethinkDbManager()
        self.valor_manager = ValorManager()


    def valor_create(self):

        aws = AWS()

        return self.valor_manager.create_valor(
            aws.get_subnet_id(),
            aws.get_sec_group().id)


    def valor_create_pool(self, number_of_valors):
        return self.valor_manager.create_valor_pool(number_of_valors)


    def valor_destroy(self, valor_id):
        return self.valor_manager.destroy_valor(valor_id)


    def valor_list(self):
        return self.rethinkdb_manager.list_valors()


    def valor_migrate_virtue(self, virtue_id, new_valor_id):
        return self.valor_manager.migrate_virtue(virtue_id, new_valor_id)



class Valor:

    aws_instance = None
    guestnet = None

    def __init__(self, valor_id):

        self.ec2 = boto3.resource('ec2')
        self.aws_instance = self.ec2.Instance(valor_id)


    def authorize_ssh_connections(self, ip):

        security_group = self.ec2.SecurityGroup(
            self.aws_instance.security_groups[0]['GroupId'])

        #TODO: should the security group already be authorized for SSH?
        try:
            security_group.authorize_ingress(
                CidrIp=ip,
                FromPort=22,
                IpProtocol='tcp',
                ToPort=22 )

        except botocore.exceptions.ClientError:
            print(
                'ClientError encountered while adding security group rule. '
                + 'Rule may already exist.')


    def get_efs_mount(self):

        #TODO: remove hardcoded stack_name
        stack_name = 'test-for-192'

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
                #TODO: Need to automatically get key in home directory
                key_filename=os.environ['HOME'] + '/starlab-virtue-te.pem')

        except Exception as error:

            print(error)
            print('SSH failed to connect')

        return client


    def setup(self):
        '''
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

        time.sleep(30)

        stdin, stdout, stderr = client.exec_command(
            copy_config_directory_command)
        print('[!] copy_config_dir : stdout : ' + stdout.read())
        print('[!] copy_config_dir : stderr : ' + stderr.read())

        time.sleep(30)

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
                    self.aws_instance.public_ip_address))

                break

            except Exception as error:
                print(error)
                print('Attempt {0} failed to connect').format(attempt_number+1)


class ValorManager:

    def __init__(self):

        self.aws = AWS()
        self.rethinkdb_manager = RethinkDbManager()
        self.router_manager = RouterManager()


    def get_empty_valor(self):

        valors = self.rethinkdb_manager.list_valors()
        virtues = self.rethinkdb_manager.list_virtues()

        empty_valor = None
        for valor in valors:

            valor_is_empty = True

            for virtue in virtues:

                if valor['address'] == virtue['address']:
                    valor_is_empty = False
                    break

            if valor_is_empty:
                empty_valor = valor
                break

        #TODO: if no empty valors are found

        return valor


    def create_valor(self, subnet, sec_group):

        excalibur_ip = '{0}/32'.format(self.aws.get_public_ip())

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

        instance = self.aws.instance_create(**valor)

        valor = Valor(instance.id)

        valor.authorize_ssh_connections(excalibur_ip)

        valor.wait_until_accessible()

        self.rethinkdb_manager.add_valor(valor)

        self.router_manager.add_valor(valor)

        valor.setup()

        return instance.id


    def create_valor_pool(self, number_of_valors):
        for index in range(number_of_valors):
            self.create_valor()
 

    def destroy_valor(self, valor_id):

        self.aws.instance_destroy(valor_id, block=False)

        self.rethinkdb_manager.remove_valor(valor_id)


    def migrate_virtue(self, virtue_id, new_valor_id):

        virtue = rethinkdb.db('transducers').table('galahad').filter({
            'function' : 'virtue',
            'host' : virtue_id}).run()

        current_valor = rethinkdb.db('transducers').table('galahad').filter({
            'function' : 'valor',
            'address' : virtue['address']}).run()

        current_valor_id = current_valor['host']




class RethinkDbManager:

    #TODO: Remove hardcoded IP and replace with DNS name
    domain_name = 'rethinkdb.galahad.com'

    def __init__(self):
        self.connection = rethinkdb.connect(
            domain_name,
            28015,
            ssl = {
                'ca_certs': '/home/ubuntu/rethinkdb_cert.pem',
            }).repl()


    def list_valors(self):

        response = rethinkdb.db('transducers').table('galahad').filter(
            {'function' : 'valor'}).run()

        valors = list(response.items)

        return valors


    def list_virtues(self):

        response = rethinkdb.db('transducers').table('galahad').filter(
            {'function' : 'virtue'}).run()

        virtues = list(response.items)

        return virtues


    def add_valor(self, valor):

        assert valor.guestnet == None

        # TODO: We need to use new guestnet for each valor
        record = {
            'function': 'valor',
            'guestnet': '10.91.0.1',
            'host'    : valor.aws_instance.id,
            'address' : valor.aws_instance.private_ip_address
        }

        rethinkdb.db('transducers').table('galahad').insert([record]).run()
        valor.guestnet = record['guestnet']


    def remove_valor(self, valor_id):

        matching_valors = list(rethinkdb.db('transducers').table('galahad').filter({
            'function': 'valor',
            'host': valor_id
        }).run())

        rethinkdb.db('transducers').table('galahad').filter(
            matching_valors[0]).delete().run()


    def get_free_guestnet(self):

        guestnet = '10.91.0.{0}'

        for test_number in range(1, 256):
            results = rethinkdb.db('transducers').table('galahad').filter({
                'guestnet': guestnet.format(test_number)
            }).run()
            if (len(list(results)) == 0):
                guestnet = guestnet.format(test_number)
                break

        # If this fails, then there was no available guestnet
        assert '{0}' not in guestnet

        return guestnet


    def add_virtue(self, valor_address, virtue_hostname, efs_path):

        matching_virtues = list(rethinkdb.db('transducers').table('galahad').filter({
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

        rethinkdb.db('transducers').table('galahad').insert([record]).run()


    def get_virtue(self, virtue_hostname):

        matching_virtues = list(rethinkdb.db('transducers').table('galahad').filter({
            'function': 'virtue',
            'host': virtue_hostname
        }).run())

        if (len(matching_virtues) != 1):
            return matching_virtues

        return matching_virtues[0]


    def remove_virtue(self, virtue_hostname):

        matching_virtues = list(rethinkdb.db('transducers').table('galahad').filter({
            'function': 'virtue',
            'host': virtue_hostname
        }).run())

        assert len(matching_virtues) == 1

        rethinkdb.db('transducers').table('galahad').filter(
            matching_virtues[0]).delete().run()


class RouterManager:

    ip_address = ''

    def add_valor(self, valor):
        pass
