import os

import boto3
import botocore
import rethinkdb
from aws import AWS
from boto.utils import get_instance_metadata
from ssh_tool import ssh_tool


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


    def valor_migrate_virtue(self, virtue_id, destination_valor_id):
        return self.valor_manager.migrate_virtue(virtue_id, destination_valor_id)



class Valor:

    aws_instance = None
    guestnet = None

    def __init__(self, valor_id):

        self.ec2 = boto3.resource('ec2')
        self.aws_instance = self.ec2.Instance(valor_id)
        self.client = None


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


    def get_stack_name(self):

        resource = boto3.resource('ec2')

        meta_data = get_instance_metadata(timeout=0.5, num_retries=2)

        myinstance = resource.Instance(meta_data['instance-id'])

        # Find the Stack name in the instance tags
        for tag in myinstance.tags:
            if 'aws:cloudformation:stack-name' in tag['Key']:
                return tag['Value']


    def get_efs_mount(self):

        stack_name = self.get_stack_name()

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

        stdout = self.client.ssh(make_efs_mount_command, output=True)
        print('[!] Valor.mount_efs : stdout : ' + stdout)

        stdout = self.client.ssh(mount_efs_command, output=True)
        print('[!] Valor.mount_efs : stdout : ' + stdout)


    def connect_with_ssh(self):

        self.client = ssh_tool(
            'ubuntu',
            self.aws_instance.public_ip_address,
            sshkey=os.environ['HOME'] +
                   '/galahad-keys/default-virtue-key.pem')

        if not self.client.check_access():
            print('Failed to connect to valor with IP {} using SSH'.format(
                self.aws_instance.public_ip_address))
            raise


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

        stdout = self.client.ssh(
            copy_config_directory_command, output=True)
        print('[!] copy_config_dir : stdout : ' + stdout)

        stdout = self.client.ssh(
            cd_and_execute_setup_command, output=True)
        print('[!] execute_setup : stdout : ' + stdout)


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

        valor.connect_with_ssh()

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


    def migrate_virtue(self, virtue_id, destination_valor_id):

        virtue = rethinkdb.db('transducers').table('galahad').filter({
            'function' : 'virtue',
            'host' : virtue_id}).run()

        current_valor = rethinkdb.db('transducers').table('galahad').filter({
            'function' : 'valor',
            'address' : virtue['address']}).run()

        current_valor_id = current_valor['host']




class RethinkDbManager:

    domain_name = 'rethinkdb.galahad.com'

    def __init__(self):
        self.connection = rethinkdb.connect(
            host = self.domain_name,
            port = 28015,
            ssl = {
                'ca_certs':'/var/private/ssl/rethinkdb_cert.pem',
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
