import os
import time

import boto3
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


    def valor_launch(self, valor_id):
        return self.valor_manager.launch_valor(valor_id)


    def valor_create_pool(self, number_of_valors):

        aws = AWS()

        return self.valor_manager.create_valor_pool(
            number_of_valors,
            aws.get_subnet_id(),
            aws.get_sec_group().id)


    def valor_stop(self, valor_id):
        return self.valor_manager.stop_valor(valor_id)


    def valor_destroy(self, valor_id):
        return self.valor_manager.destroy_valor(valor_id)


    def valor_list(self):
        return self.rethinkdb_manager.list_valors()


    def valor_migrate_virtue(self, virtue_id, destination_valor_id):
        return self.valor_manager.migrate_virtue(
            virtue_id,
            destination_valor_id)



class Valor:

    def __init__(self, valor_id):

        self.ec2 = boto3.resource('ec2')
        self.aws_instance = self.ec2.Instance(valor_id)
        self.client = None
        self.guestnet = None
        self.router_ip = None


    def connect_with_ssh(self):

        self.client = ssh_tool(
            'ubuntu',
            self.aws_instance.private_ip_address,
            sshkey=os.environ['HOME'] +
                   '/galahad-keys/default-virtue-key.pem')

        if not self.client.check_access():
            print('Failed to connect to valor with IP {} using SSH'.format(
                self.aws_instance.private_ip_address))
            raise Exception(
                'Failed to connect to valor with IP {} using SSH'.format(self.aws_instance.private_ip_address))


    def setup(self):
        '''
        ovs-vsctl show - see bridge to remote router
        xl list - received:
            `Domain-0                       0  2048     2     r-----     198.6`
        ping 10.91.0.254 - should work
        '''

        #self.mount_efs()

        check_if_cloud_init_finished = \
            '''while [ ! -f /var/lib/cloud/instance/boot-finished ]; do
                   echo "Cloud init has not finished";sleep 5;done;
               echo "Cloud init has now finished"'''

        execute_setup_command = \
            'cd /mnt/efs/valor/deploy/compute && sudo /bin/bash setup.sh "{0}" "{1}"'.format(
                self.guestnet, self.router_ip)

        setup_gaius_command = \
            'cd /mnt/efs/valor && sudo /bin/bash setup_gaius.sh'

        setup_syslog_ng_command = \
            'cd /mnt/efs/valor/ && sudo /bin/bash setup_syslog_ng.sh'

        shutdown_node_command = \
            'sudo shutdown -h now'

        stdout = self.client.ssh(
            check_if_cloud_init_finished, output=True)
        print('[!] check_cloud_init : stdout : ' + stdout)

        stdout = self.client.ssh(
            execute_setup_command, output=True)
        print('[!] execute_setup : stdout : ' + stdout)

        stdout = self.client.ssh(
            setup_gaius_command, output=True)
        print('[!] setup_gaius : stdout : ' + stdout)

        stdout = self.client.ssh(
            setup_syslog_ng_command, output=True)
        print('[!] setup_syslog_ng : stdout : ' + stdout)

        try:
            stdout = self.client.ssh(
                shutdown_node_command, output=True)
            print('[!] shutdown_node : stdout : ' + stdout)
        except:
            # TODO
            # Currently the shutdown command is issued it causes immediate disconnect
            # and ssh_tool throws an error due to that.
            # Ignore the error for now
            pass


    def verify_setup(self):

        # Verify the Valor Setup

        # TODO: Currently the test below fails as the command is issued
        #       too soon after the reboot and Xen services are still coming up.
        #       Figure out a way to handle this condition.
        # Verify that Xen xl command works
        execute_xl_list_command = \
            'sudo xl list'

        try:
            stdout = self.client.ssh(execute_xl_list_command, output=True)
            print('[!] verify_Xen : stdout : ' + stdout)

        except Exception as error:

            print(error)
            print('need to wait to reboot before verifying')

        # Verify connectivity to rethinkDB
        # Verify EFS mount point exists and is accessible
        # Verify  that gaius service is up and running
        return True


class ValorManager:

    def __init__(self):

        self.aws = AWS()
        self.rethinkdb_manager = RethinkDbManager()
        self.router_manager = RouterManager()
        self.setup_syslog_config()


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

        return file_system_id

    def get_empty_valor(self):

        valors = self.rethinkdb_manager.list_valors()
        virtues = self.rethinkdb_manager.list_virtues()

        for valor in valors:

            valor_is_empty = True

            for virtue in virtues:

                if valor['address'] == virtue['address']:
                    valor_is_empty = False
                    break

            if valor_is_empty:
                # return this empty valor
                return valor

        # If no empty valors are found then create a valor
        aws = AWS()

        valor_id = self.create_valor(
            aws.get_subnet_id(),
            aws.get_sec_group().id)

        self.launch_valor(valor_id)

        return self.rethinkdb_manager.get_valor(valor_id)


    def create_valor(self, subnet, sec_group):

        # Use cloud init to install the base packages for the valor
        user_data = '''#!/bin/bash -xe
                       # Install Packages required for AWS EFS mount helper
                       apt-get update
                       apt-get -y install binutils

                       # Install the AWS EFS mount helper
                       git clone https://github.com/aws/efs-utils
                       cd efs-utils/
                       ./build-deb.sh
                       apt-get -y install ./build/amazon-efs-utils*deb

                       # Create the base mount directory
                       mkdir -p /mnt/efs

                       # Mount the EFS file system
                       echo "{}:/ /mnt/efs efs defaults,_netdev 0 0" >> /etc/fstab
                       mount -a

                       # Install System packages
                       apt-get -y install python-pip openvswitch-common openvswitch-switch bridge-utils

                       # Install pip packages
                       pip install rethinkdb
                    '''.format(self.get_efs_mount())

        valor_config = {
            'image_id' : 'ami-01c5d8354c604b662',
            'inst_type' : 't2.medium',
            'subnet_id' : subnet,
            'key_name' : 'starlab-virtue-te',
            'tag_key' : 'Project',
            'tag_value' : 'Virtue',
            'sec_group' : sec_group,
            'inst_profile_name' : '',
            'inst_profile_arn' : '',
            'user_data': user_data,
        }

        instance = self.aws.instance_create(**valor_config)

        valor = Valor(instance.id)

        valor.connect_with_ssh()

        self.rethinkdb_manager.add_valor(valor)

        self.router_manager.add_valor(valor)

        valor.setup()

        # valor.verify_setup()

        instance.wait_until_stopped()
        instance.reload()

        return instance.id


    def launch_valor(self, valor_id):

        instance = self.aws.instance_launch(valor_id)

        # Wait for 20 seconds for valor node to start
        time.sleep(20)

        valor = Valor(valor_id)

        valor.connect_with_ssh()

        return instance.id


    def create_valor_pool(
        self,
        number_of_valors,
        subnet,
        sec_group):

        valor_ids = []

        for index in range(int(number_of_valors)):

            valor_id = self.create_valor(subnet, sec_group)
            valor_ids.append(valor_id)

        return valor_ids


    def stop_valor(self, valor_id):

        instance = self.aws.instance_stop(valor_id)

        return instance.id 


    def destroy_valor(self, valor_id):

        self.aws.instance_destroy(valor_id, block=False)

        self.rethinkdb_manager.remove_valor(valor_id)


    def migrate_virtue(self, virtue_id, destination_valor_id):

        virtue = rethinkdb.db('transducers').table('galahad').filter({
            'function' : 'virtue',
            'virtue_id' : virtue_id}).run().next()

        current_valor = rethinkdb.db('transducers').table('galahad').filter({
            'function' : 'valor',
            'address' : virtue['address']}).run().next()


        destination_valor = rethinkdb.db('transducers').table('galahad').filter({
            'function' : 'valor',
            'valor_id' : destination_valor_id}).run().next()

        current_valor_ip_address = current_valor['address']
        destination_valor_ip_address = destination_valor['address']

        rethinkdb.db("transducers").table("commands") \
            .filter({"valor_ip": current_valor_ip_address}) \
            .update({"valor_dest": destination_valor_ip_address}).run()

        rethinkdb.db("transducers").table("commands") \
            .filter({"valor_ip": current_valor_ip_address}) \
            .update({"enabled": True}).run()

    def setup_syslog_config(self):
        # Todo:  Make this configurable
        conf_dir = '/home/ubuntu/galahad/valor/syslog-ng/'
        mount_dir = '/mnt/efs/valor/syslog-ng/'
        aggregator_node = 'https://aggregator.galahad.com:9200'
        aggregator_host = "aggregator.galahad.com"
        syslog_ng_server = "172.30.128.131"

        # Create syslog-ng.conf from
        #   payload/syslog-ng-virtue-node.conf.template
        with open(conf_dir + '/syslog-ng-valor-node.conf.template',
                  'r') as t:
            syslog_ng_config = t.read()
            with open(mount_dir + '/syslog-ng.conf', 'w') as f:
                f.write(syslog_ng_config % (aggregator_node,
                                            syslog_ng_server))
        # Create elasticsearch.yml from ELASTIC_YML
        with open(conf_dir + '/elasticsearch.yml.template', 'r') as t:
            elastic_yml = t.read()
            with open(mount_dir + '/elasticsearch.yml',
                      'w') as f:
                f.write(elastic_yml % (aggregator_host))



class RethinkDbManager:

    domain_name = 'rethinkdb.galahad.com'

    def __init__(self):

        try:
            self.connection = rethinkdb.connect(
                host = self.domain_name,
                port = 28015,
                ssl = {
                    'ca_certs':'/var/private/ssl/rethinkdb_cert.pem',
                }).repl()

        except Exception as error:
            print(error)


    def get_valor(self, valor_id):

        response = rethinkdb.db('transducers').table('galahad').filter(
            {'function': 'valor', 'valor_id': valor_id}).run()

        valor = list(response.items)

        # Return the first item in the list as there should only be 1 valor entry
        # corresponding to the specified valor_id
        return valor[0]

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

        record = {
            'function': 'valor',
            'guestnet': self.get_free_guestnet(),
            'valor_id'    : valor.aws_instance.id,
            'address' : valor.aws_instance.private_ip_address
        }

        rethinkdb.db('transducers').table('galahad').insert([record]).run()

        valor.guestnet = record['guestnet']

        valor.router_ip = self.get_router()['address']


    def remove_valor(self, valor_id):

        matching_valors = list(rethinkdb.db('transducers').table('galahad').filter({
            'function': 'valor',
            'valor_id': valor_id
        }).run())

        rethinkdb.db('transducers').table('galahad').filter(
            matching_valors[0]).delete().run()


    def get_free_guestnet(self):

        guestnet = '10.91.0.{0}'

        for test_number in range(1, 256):
            results = rethinkdb.db('transducers').table('galahad').filter({
                'guestnet': guestnet.format(test_number)
            }).run()
            if len(list(results)) == 0:
                guestnet = guestnet.format(test_number)
                break

        # If this fails, then there was no available guestnet
        assert '{0}' not in guestnet

        return guestnet


    def add_virtue(self, valor_address, valor_id, virtue_id, efs_path, role_create=False):

        matching_virtues = list(rethinkdb.db('transducers').table('galahad').filter({
            'function': 'virtue',
            'virtue_id': virtue_id
        }).run())

        assert len(matching_virtues) == 0

        guestnet = self.get_free_guestnet()

        record = {
            'function'  : 'virtue',
            'virtue_id' : virtue_id,
            'valor_id'  : valor_id,
            'address'   : valor_address,
            'guestnet'  : guestnet,
            'img_path'  : efs_path
        }
        rethinkdb.db('transducers').table('galahad').insert([record]).run()

        if not role_create:
            trans_migration = rethinkdb.db('transducers').table('commands')\
                .filter({'virtue_id': virtue_id, 'transducer_id': 'migration'}).run().next()
            trans_introspection = rethinkdb.db('transducers').table('commands')\
                .filter({'virtue_id': virtue_id, 'transducer_id': 'introspection'}).run().next()

            trans_migration['valor_ip'] = valor_address
            trans_migration['valor_dest'] = None
            trans_migration['history'] = None
            rethinkdb.db('transducers').table('commands').filter({'virtue_id': virtue_id,
                'transducer_id': 'migration'}).update(trans_migration).run()

            trans_introspection['valor_id'] = valor_id
            trans_introspection['interval'] = 10
            trans_introspection['comms'] = []
            rethinkdb.db('transducers').table('commands').filter({'virtue_id': virtue_id,
                'transducer_id': 'introspection'}).update(trans_introspection).run()

        return guestnet


    def get_virtue(self, virtue_id):

        matching_virtues = list(rethinkdb.db('transducers').table('galahad').filter({
            'function': 'virtue',
            'virtue_id': virtue_id
        }).run())

        if len(matching_virtues) != 1:
            return matching_virtues

        return matching_virtues[0]


    def remove_virtue(self, virtue_id):

        matching_virtues = list(rethinkdb.db('transducers').table('galahad').filter({
            'function': 'virtue',
            'virtue_id': virtue_id
        }).run())

        assert len(matching_virtues) == 1

        rethinkdb.db('transducers').table('galahad').filter(
            matching_virtues[0]).delete().run()

    
    def destroy_virtue(self, virtue_id):
        rethinkdb.db('transducers').table('commands').filter(
            {'virtue_id', virtue_id}).delete().run()


    def get_router(self):

        router = rethinkdb.db('transducers').table('galahad').filter({
            'function': 'router' }).run()

        return router.next()


class RouterManager:

    def __init__(self):

        self.ip_address = None
        self.client = None

    def add_valor(self, valor):
        # Call into router to add port to ovs bridge for the
        # valor being added to the system

        self.ip_address = valor.router_ip

        self.connect_with_ssh()

        add_valor_command = \
            'cd /mnt/efs/valor/deploy/router && sudo /bin/bash add_valor.sh "{0}"'.format(
                valor.aws_instance.private_ip_address)

        stdout = self.client.ssh(
            add_valor_command, output=True)
        print('[!] add_valor_command : stdout : ' + stdout)


    def connect_with_ssh(self):

        self.client = ssh_tool(
            'ubuntu',
            self.ip_address,
            sshkey=os.environ['HOME'] +
                   '/galahad-keys/default-virtue-key.pem')

        if not self.client.check_access():
            print('Failed to connect to valor with IP {} using SSH'.format(
                self.ip_address))
            raise Exception(
                'Failed to connect to valor with IP {} using SSH'.format(self.ip_address))
