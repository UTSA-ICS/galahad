import boto3
import rethinkdb

from paramiko import SSHClient

from aws import AWS


class ValorAPI:

    def __init__(self):

        self.rethinkdb = RethinkDbManager()


    def valor_create(self):
        aws = AWS()
        ValorManaager.create_valor(aws.get_subnet_id(), aws.get_sec_group())
      
 
    def valor_create_pool(self):
        pass


    def valor_destroy(self):
        pass


    def valor_list(self):
        return self.rethinkdb.list_valors()



class Valor: 

    def __init__(self, subnet, sec_group):

        aws = AWS()

        excalibur_ip = '{0}/32'.format(aws.get_public_ip())
        self.subnet    = subnet
        self.sec_group = sec_group
        self.guestnet  = None

        valor = {
            'image_id' : 'ami-01c5d8354c604b662',
            'inst_type' : 't2.small',
            'subnet_id' : self.subnet,
            'key_name' : 'startlab-virtue-te', 
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
        sg = ec2.SecurityGroup(self.sec_group)

        #TODO: should the security group already be authorized for SSH?
        try:
            self.sg.authorize_ingress(
                CidrIp=ip,
                FromPort=22,
                IpProtocol='tcp',
                ToPort=22 
            )

        except botocore.exceptions.ClientError:
            print(
                'ClientError encountered while adding sec group rule. '
                + 'Rule may already exist.')


    def mount_efs(self):

        mount_efs_command = (
            'sudo mount -t nfs '
            'fs-de078b96.efs.us-east-1.amazonaws.com:/export '
            '/mnt/efs/')

        client = self.connect_with_ssh()

        stdin, stdout, stderr = client.exec_command(mount_efs_command)

        print('[!] Valor.mount_efs : stdout : ' + stdout.readlines())
        print('[!] Valor.mount_efs : stderr : ' + stderr.readlines())


    def connect_with_ssh(self):

        client = SSHClient()

        client.load_system_host_keys()
        client.connect(self.aws_instance.public_ip_address, 'ubuntu')

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
        virtue_guestnet = '10.91.0.5'

        # Write to rethink


class ValorManager:

    rethinkdb_ip_address = ''


    def get_empty_valor(self):
        pass


    def create_valor(self, subnet):

        valor = Valor(subnet)
        valor.mount_efs()

        RethinkDbManager.add_valor(valor)

        RouterManager.add_valor(valor)

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

        return valor_list


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


    def add_virtue(self, virtue_hostname, efs_path):

        # TODO: How do we decide what address and guestnet to use?
        record = {
            'function': 'virtue',
            'host'    : virtue_hostname,
            'address' : '172.30.87.98',
            'guestnet': '10.91.0.5',
            'efs_path': efs_path
        }

        rethinkdb.db('routing').table('galahad').insert([record]).run()


class RouterManager:

    ip_address = ''

    def add_valor(self, valor):
        pass
