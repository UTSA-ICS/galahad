import os
import threading
import time

import boto3
import rethinkdb
from boto.utils import get_instance_metadata

from aws import AWS
from ssh_tool import ssh_tool

NUM_STANDBY_VALORS = 3

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

        file_system_id = ''

        for output in efs_stack.outputs:

            if output['OutputKey'] == 'FileSystemID':
                file_system_id = output['OutputValue']

        return file_system_id

    def get_empty_valors(self, valors, virtues):
        empty_valors = []
        for valor in valors:
            if valor['valor_id'] not in str(virtues):
                empty_valors.append(valor)

        return empty_valors


    def get_empty_valor(self):
        """ Get and return an available valor node.
        If less than the standby number of valors exist then
        create more standby valors
        """

        valors = self.rethinkdb_manager.list_valors()
        virtues = self.rethinkdb_manager.list_virtues()

        empty_valors = self.get_empty_valors(valors, virtues)

        aws = AWS()

        # Check if the number of empty valors is less than NUM_STANDBY_VALORS
        # If so then create additional valors
        if (len(empty_valors) - 1) <= NUM_STANDBY_VALORS:

            if not empty_valors:
                valor_ids = self.create_valor_pool(1, aws.get_subnet_id(), aws.get_sec_group().id)

                for i in range(NUM_STANDBY_VALORS):
                    create_standby_valors_thread = threading.Thread(target=self.create_valor,
                                                                    args=(aws.get_subnet_id(),
                                                                          aws.get_sec_group().id,))
                    create_standby_valors_thread.start()

                # Check the valor state and verify that it is 'RUNNING'
                self.verify_valor_running(valor_ids[0])

                return self.rethinkdb_manager.get_valor(valor_ids[0])

            # Number of standby valors to create: 1 less than the number of available valors
            # as 1 will be used when it will be returned by this method.
            NUM_VALORS_TO_CREATE = NUM_STANDBY_VALORS - (len(empty_valors) - 1)

            for i in range(NUM_VALORS_TO_CREATE):
                create_standby_valors_thread = threading.Thread(target=self.create_valor,
                                                                args=(aws.get_subnet_id(),
                                                                      aws.get_sec_group().id,))
                create_standby_valors_thread.start()

            # Check the valor state and verify that it is 'RUNNING'
            self.verify_valor_running(empty_valors[0]['valor_id'])

            return empty_valors[0]

        elif len(empty_valors) > NUM_STANDBY_VALORS:
            # Number of Empty Valors is more than the required number of standby Valors
            # so do nothing

            # Check the valor state and verify that it is 'RUNNING'
            self.verify_valor_running(empty_valors[0]['valor_id'])

            return empty_valors[0]


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

        # Not using self.rethinkdb_manager variable here as when create_valor
        # is called using a separate thread in get_empty_valor() the
        # self.rethinkdb_manager variable is not initialized as the
        # initialization is done in the ValorManager constructor.
        RethinkDbManager().add_valor(valor)

        # Not using self.router_manager variable here as when create_valor
        # is called using a separate thread in get_empty_valor() the
        # self.router_manager variable is not initialized as the
        # initialization is done in the ValorManager constructor.
        RouterManager().add_valor(valor)

        valor.setup()

        # valor.verify_setup()

        instance.wait_until_stopped()
        instance.reload()

        # Not using self.rethinkdb_manager variable here as when create_valor
        # is called using a separate thread in get_empty_valor() the
        # self.rethinkdb_manager variable is not initialized as the
        # initialization is done in the ValorManager constructor.
        RethinkDbManager().set_valor(valor.aws_instance.id, 'state', 'STOPPED')

        return instance.id


    def launch_valor(self, valor_id):

        instance = self.aws.instance_launch(valor_id)

        # Wait for 20 seconds for valor node to start
        time.sleep(20)

        valor = Valor(valor_id)

        valor.connect_with_ssh()

        self.rethinkdb_manager.set_valor(valor_id, 'state', 'RUNNING')

        return instance.id


    def verify_valor_running(self, valor_id):

        # Check the valor state and verify that it is 'RUNNING'
        valor_state = self.rethinkdb_manager.get_valor(valor_id)['state']

        while valor_state != 'RUNNING':
            if valor_state == 'STOPPED':
                self.launch_valor(valor_id)
                break
            elif valor_state == 'CREATING':
                time.sleep(30)
                valor_state = self.rethinkdb_manager.get_valor(valor_id)['state']
            else:
                Exception('Unexpected Error condition encountered while getting a valor')

    def create_valor_pool(
        self,
        number_of_valors,
        subnet,
        sec_group):

        valor_ids = []

        for index in range(int(number_of_valors)):

            valor_id = self.create_valor(subnet, sec_group)
            valor_ids.append(valor_id)

        for valor_id in valor_ids:
            self.launch_valor(valor_id)

        return valor_ids


    def stop_valor(self, valor_id):

        instance = self.aws.instance_stop(valor_id)

        self.rethinkdb_manager.set_valor(valor_id, 'state', 'STOPPED')

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

    def set_valor(self, valor_id, key, value):

        valor_query = rethinkdb.db('transducers').table('galahad').filter(
            {'function': 'valor', 'valor_id': valor_id})

        valor_query.update({key: value}).run()

        return self.get_valor(valor_id)

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
            'valor_id': valor.aws_instance.id,
            'address' : valor.aws_instance.private_ip_address,
            'state'   : 'CREATING'
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

        lock = threading.Lock()

        lock.acquire()

        try:
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
        finally:
            lock.release()

        return guestnet


    def add_virtue(self, valor_address, valor_id, virtue_id, efs_path):

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
