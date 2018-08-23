import boto3
import rethinkdb

from paramiko import SSHClient


class ValorAPI:


    def valor_create(self):
        ValorManaager.create_valor()
      
 
    def valor_create_pool(self):
        pass


    def valor_destroy(self):
        pass


    def valor_list(self):
        pass



class Valor: 

    def __init__(self):

        aws = AWS()

        #TODO: need ip of valor, not excalibur 
        self.ip = '{0}/32'.format(aws.get_public_ip())
        self.subnet    = aws.get_subnet_id
        self.sec_group = aws.get_sec_group()

        self.authorize_ssh_connections()

        valor = {
            'image_id' : 'ami-01c5d8354c604b662',
            'inst_type' : 't2.small',
            'subnet_id' : self.subnet,
            'key_name' : 'startlab-virtue-te', 
            'tag_key' : 'Project',
            'tag_value' : 'Virtue',
            'sec_group' : self.sec_group.id,
            'inst_profile_name' : '',
            'inst_profile_arn' : '', 
        }

        instance = aws.instance_create(**valor)

        return instance


    def authorize_ssh_connections(self):

        #TODO: should the security group already be authorized for SSH?
        try:
            self.sec_group.authorize_ingress(
                CidrIp=self.ip,
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
            'sudo mount -t nfs 
            fs-de078b96.efs.us-east-1.amazonaws.com:/export
            /mnt/efs/')

        client = self.connect_with_ssh()

        stdin, stdout, stderr = client.exec_command(mount_efs_command)

        print('[!] Valor.mount_efs : stdout : ' + stdout.readlines())
        print('[!] Valor.mount_efs : stderr : ' + stderr.readlines())


    def connect_with_ssh(self):

        client = SSHClient()

        client.load_system_host_keys()
        client.connect(self.ip, 'ubuntu')

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
        


class ValorManager:

    rethinkdb_ip_address = ''


    def get_empty_valor(self)
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

    ip_address = ''

    def __init__(self):
        client = rethinkdb.connect(ip_address, 28015).repl()


    def list_valors(self):
        return r.db('routing').table('galahad').run()


    def add_valor(self, valor):

        record = {
           'function' : 'valor',
           'guestnet' : '10.91.0.1',
            'host'    : valor.public_dns_name
            'address' : valor.private_ip_address
        }

        self.client.db('routing').table('galahad').insert([{record}]).run()



class RouterManager:

    ip_address = ''

    def add_valor(self, valor):
        pass
