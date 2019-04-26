# Copyright (c) 2019 by Star Lab Corp.

import os
import random
import threading
import time
import subprocess

import boto3
import rethinkdb
from boto.utils import get_instance_metadata

from aws import AWS
from ssh_tool import ssh_tool

# Number of MAX standby valors to keep provisioned
NUM_STANDBY_VALORS = 1

# number of max virtues per valor
MAX_VIRTUES_PER_VALOR = 3

# Default of 5 minutes interval between migration runs
AUTO_MIGRATION_INTERVAL = 300

# Global lock variable to prevent more than 1 thread from accessing
# get_free_guestnet()
lock = threading.Lock()


class ValorAPI:

    def __init__(self):

        self.valor_manager = ValorManager()


    def valor_create(self):

        aws = AWS()

        return self.valor_manager.create_valor(aws.get_subnet_id(),
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
        return self.valor_manager.list_valors()


    def auto_migration_start(self, migration_interval=AUTO_MIGRATION_INTERVAL):
        if not self.is_auto_migration_on():
            self.valor_manager.auto_migration_start(migration_interval)
            auto_migration_thread = threading.Thread(target=self.auto_migration,
                                                     args=(migration_interval,))
            auto_migration_thread.start()


    def auto_migration_stop(self):
        if self.is_auto_migration_on():
            self.valor_manager.auto_migration_stop()


    def auto_migration_status(self):
        return self.valor_manager.auto_migration_status()


    def is_auto_migration_on(self):
        return self.valor_manager.is_auto_migration_on()


    def auto_migration(self, migration_interval):
        while self.is_auto_migration_on():
            virtues = self.valor_manager.list_virtues()
            for virtue in virtues:
                self.valor_migrate_virtue(virtue['virtue_id'])
            # Now sleep for AUTO_MIGRATION_INTERVAL before starting another migration
            # run for ALL virtues
            time.sleep(migration_interval)


    def valor_migrate_virtue(self, virtue_id, destination_valor_id=None):
        # Get virtue's current valor
        source_valor_id = self.valor_manager.get_valor_for_virtue(virtue_id)['valor_id']

        # If no destination valor is specified then select an available one
        if destination_valor_id == None:
            destination_valor = self.valor_manager.get_empty_valor(source_valor_id)
            destination_valor_id = destination_valor['valor_id']
        elif source_valor_id == destination_valor_id:
            raise Exception(('ERROR: Source valor [{0}] and Destination Valor [{1}] '
                             'are the same'.format(source_valor_id,
                                                   destination_valor_id)))

        self.valor_manager.migrate_virtue(virtue_id, destination_valor_id)

        return destination_valor_id


class Valor:

    def __init__(self, valor_id):

        self.ec2 = boto3.resource('ec2')
        self.aws_instance = self.ec2.Instance(valor_id)
        self.client = None
        self.guestnet = None


    def connect_with_ssh(self):

        self.client = ssh_tool(
            'ubuntu',
            self.aws_instance.private_ip_address,
            sshkey=os.environ['HOME'] +
                   '/user-keys/default-virtue-key.pem')

        if not self.client.check_access():
            print('Failed to connect to valor with IP {} using SSH'.format(
                self.aws_instance.private_ip_address))
            raise Exception(
                'ERROR: Failed to connect to valor with IP {} using SSH'.format(
                    self.aws_instance.private_ip_address))


    def setup(self, router_ip):

        check_if_cloud_init_finished = \
            '''while [ ! -f /var/lib/cloud/instance/boot-finished ]; do
                   echo "Cloud init has not finished";sleep 5;done;
               echo "Cloud init has now finished"'''

        execute_setup_ovs_bridge_command = \
            'cd /mnt/efs/valor/deploy/compute &&' \
            'sudo /bin/bash setup_ovs_bridge.sh "{0}" "{1}"'.format(
                self.guestnet, router_ip)

        shutdown_node_command = \
            'sudo shutdown -h now'

        stdout = self.client.ssh(
            check_if_cloud_init_finished, output=True)
        print('[!] check_cloud_init : stdout : ' + stdout)

        stdout = self.client.ssh(
            execute_setup_ovs_bridge_command, output=True)
        print('[!] execute_setup_ovs_bridge : stdout : ' + stdout)

        try:
            stdout = self.client.ssh(
                shutdown_node_command, output=True)
            print('[!] shutdown_node : stdout : ' + stdout)
        except:
            # TODO
            # Currently the shutdown command is issued it causes immediate
            # disconnect and ssh_tool throws an error due to that.
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

    def get_valor_for_virtue(self, virtue_id):
        # Go through the list of valors and return the valor that has the specified
        # virtue running on it.
        for valor in self.list_valors():
            for virtue in valor['virtues']:
                if virtue == virtue_id:
                    return valor

    def get_available_valors(self, migration_source_valor_id=None):

        if not migration_source_valor_id:
            # Return valors that have the required number of virtues
            return [valor for valor in self.list_valors() if
                    (len(valor.get('virtues', [])) < MAX_VIRTUES_PER_VALOR) and (
                                valor['state'] == 'RUNNING')]
        else:
            # Return valors that have the required number of virtues and that do not
            # match the migration source valor
            return [valor for valor in self.list_valors() if
                    (len(valor.get('virtues', [])) < MAX_VIRTUES_PER_VALOR) and
                    (valor['state'] == 'RUNNING') and
                    (valor['valor_id'] != migration_source_valor_id)]


    def get_empty_valors(self):

        # Return valors that have no virtues on them
        return [valor for valor in self.list_valors()
                if len(valor['virtues']) == 0]

    def create_and_launch_valor(self, subnet_id, security_group_id):

        valor_id = self.create_valor(subnet_id, security_group_id)

        self.launch_valor(valor_id)

        return valor_id

    def create_standby_valors(self):

        empty_valors = self.get_available_valors()

        # Check if the number of empty valors is less than NUM_STANDBY_VALORS
        # If so then create additional valors
        if len(empty_valors) <= NUM_STANDBY_VALORS:

            NUM_VALORS_TO_CREATE = NUM_STANDBY_VALORS - len(empty_valors)

            aws = AWS()

            for i in range(NUM_VALORS_TO_CREATE):
                create_standby_valors_thread = threading.Thread(
                    target=self.create_and_launch_valor,
                    args=(aws.get_subnet_id(),
                          aws.get_sec_group().id,))
                create_standby_valors_thread.start()

        elif len(empty_valors) > NUM_STANDBY_VALORS:
            # Number of empty valors is more than the required number of
            # standby valors so do nothing
            pass

    def get_empty_valor(self, migration_source_valor_id=None):
        """ Get and return an available valor node.
        If less than the standby number of valors exist then
        create more standby valors
        """

        empty_valors = self.get_available_valors(migration_source_valor_id)

        # Check if there are no empty valors
        # If there are none then create a valor node
        if not empty_valors:
            aws = AWS()
            valor_id = self.create_and_launch_valor(aws.get_subnet_id(),
                                                    aws.get_sec_group().id)

            # Check the valor state and verify that it is 'RUNNING'
            self.verify_valor_running(valor_id)

            empty_valor = self.rethinkdb_manager.get_valor(valor_id)
        else:
            # Select a random index for the array of empty_valors
            # This essentially selects a random valor from the list of valors
            random_index = random.randint(0, len(empty_valors) - 1)

            # Check the valor state and verify that it is 'RUNNING'
            self.verify_valor_running(empty_valors[random_index]['valor_id'])

            empty_valor = empty_valors[random_index]

        return empty_valor

    def list_valors(self):

        valors = self.rethinkdb_manager.list_valors()
        virtues = self.rethinkdb_manager.list_virtues()

        # Update each valor field with a virtues field.
        [valor.update({'virtues': []}) for valor in valors]

        # Update valors list with associated virtues for each valor
        for valor in valors:
            for virtue in virtues:
                if (valor['valor_id'] == virtue['valor_id']):
                    valor['virtues'].append(virtue['virtue_id'])

        return valors

    def create_valor(self, subnet, sec_group):

        # Base Setup
        with open('/mnt/efs/valor/deploy/compute/' + 'setup.sh', 'r') as f:
            base_setup_data = f.read()
        base_setup_data = base_setup_data.replace('${1}', self.get_efs_mount())

        # Xenblanket Setup
        with open('/mnt/efs/valor/deploy/compute/' + 'setup_xenblanket.sh',
                  'r') as f:
            xenblanket_setup_data = f.read()

        # Gaius Setup
        with open('/mnt/efs/valor/deploy/compute/' + 'setup_gaius.sh',
                  'r') as f:
            gaius_setup_data = f.read()

        # Syslog-ng Setup
        with open('/mnt/efs/valor/deploy/compute/' + 'setup_syslog_ng.sh',
                  'r') as f:
            syslog_ng_setup_data = f.read()

        user_data = base_setup_data + xenblanket_setup_data + \
                    gaius_setup_data + syslog_ng_setup_data

        valor_config = {
            'image_id' : 'ami-01c5d8354c604b662',
            'inst_type' : 't2.xlarge',
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

        self.setup_valor(instance)

        return instance.id


    def setup_valor(self, instance):

        router_ip = self.rethinkdb_manager.get_router()['address']

        valor = Valor(instance.id)

        valor.connect_with_ssh()

        self.rethinkdb_manager.add_valor(valor)

        # Add the valor node to the router
        RouterManager(router_ip).add_valor(valor)

        valor.setup(router_ip)

        # valor.verify_setup()

        instance.wait_until_stopped()
        instance.reload()

        self.rethinkdb_manager.set_valor(valor.aws_instance.id, 'state',
                                         'STOPPED')

        return instance.id


    def launch_valor(self, valor_id):

        instance = self.aws.instance_launch(valor_id)

        Valor(valor_id).connect_with_ssh()

        self.rethinkdb_manager.set_valor(valor_id, 'state', 'RUNNING')

        valor_ip = self.rethinkdb_manager.get_valor(valor_id)['address']

        # Add NFS export line for valor to access email preferences dir
        try:
            line = subprocess.check_output("grep mnt/ost /etc/exports", shell=True).strip("\n")
            line_num = subprocess.check_output("sed -n '/mnt\/ost/=' /etc/exports", shell=True).strip("\n")

            # Remove current line and replace with updated export
            ret = subprocess.check_call("sudo sed -i '{}d' /etc/exports".format(line_num), shell=True)
            assert ret == 0

            line+= " {}(rw,sync,no_subtree_check)".format(valor_ip)
            ret = subprocess.check_call('echo "{}" | sudo tee -a /etc/exports'.format(line), shell=True)
            assert ret == 0

            ret = subprocess.check_call(['sudo', 'exportfs', '-ra'])
            assert ret == 0

        except Exception as e:
            print("Failed to append to NFS exports with message: {}".format(e))

        return instance.id


    def verify_valor_running(self, valor_id):

        # Check the valor state and verify that it is 'RUNNING'
        valor_state = self.rethinkdb_manager.get_valor(valor_id)['state']

        valor_wait_timeout = 60
        valor_wait_count = 0

        while valor_state != 'RUNNING':

            if valor_state == 'STOPPED':
                self.launch_valor(valor_id)
                break

            elif valor_state == 'CREATING':
                time.sleep(10)
                valor_state = self.rethinkdb_manager.get_valor(valor_id)['state']
                valor_wait_count = valor_wait_count + 1

            elif valor_wait_count >= valor_wait_timeout:
                Exception('ERROR: Timed out waiting for valor to reach '
                          '[RUNNING] state - current state is [{}]'.format(
                    valor_state))

            else:
                Exception('ERROR: Unexpected Error condition encountered while getting a '
                          'valor')


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

        valor_found = False
        for valor in self.get_empty_valors():
            if valor_id == valor['valor_id']:
                valor_found = True

        if valor_found:
            instance = self.aws.instance_stop(valor_id)

            self.rethinkdb_manager.set_valor(valor_id, 'state', 'STOPPED')

            valor_ip = self.rethinkdb_manager.get_valor(valor_id)['address']

            # Remove NFS export entry
            try:
                line = subprocess.check_output("grep mnt/ost /etc/exports", shell=True).strip("\n")
                line_num = subprocess.check_output("sed -n '/mnt\/ost/=' /etc/exports", shell=True).strip("\n")

                # Remove current line and replace with updated export
                ret = subprocess.check_call("sudo sed -i '{}d' /etc/exports".format(line_num), shell=True)
                assert ret == 0

                line = line.replace(" {}(rw,sync,no_subtree_check)".format(valor_ip), "")
                ret = subprocess.check_call('echo "{}" | sudo tee -a /etc/exports'.format(line), shell=True)
                assert ret == 0

                ret = subprocess.check_call(['sudo', 'exportfs', '-ra'])
                assert ret == 0

            except Exception as e:
                print("Failed to remove NFS export with message: {}".format(e))

            return instance.id

        else:
            virtues_on_valor = [valor['virtues'] for valor in self.list_valors() if
                                valor['valor_id'] == valor_id]
            # If no valors are found then the valor_id does not exist
            if len(virtues_on_valor) == 0:
                raise Exception(
                    'ERROR: No Valor exists with the specified valor_id {}'.format(
                        valor_id))
            else:
                raise Exception(
                    'ERROR: Valor currently has the following Virtue/s running on it: '
                    '{}'.format(virtues_on_valor))

    def destroy_valor(self, valor_id):

        valor_found = False
        for valor in self.get_empty_valors():
            if valor_id == valor['valor_id']:
                valor_found = True

        if valor_found:
            self.create_standby_valors()

            self.aws.instance_destroy(valor_id, block=False)

            self.rethinkdb_manager.remove_valor(valor_id)

            return valor_id
        else:
            virtues_on_valor = [valor['virtues'] for valor in self.list_valors()
                                if valor['valor_id'] == valor_id]
            # If no valors are found then the valor_id does not exist
            if len(virtues_on_valor) == 0:
                raise Exception(
                    'ERROR: No Valor exists with the specified valor_id {}'.format(
                        valor_id))
            else:
                raise Exception(
                    'ERROR: Valor currently has the following Virtue/s running on it: '
                    '{}'.format(virtues_on_valor))

    def migrate_virtue(self, virtue_id, destination_valor_id):

        virtue = self.rethinkdb_manager.get_virtue(virtue_id)

        current_valor = rethinkdb.db('transducers').table('galahad').filter({
            'function' : 'valor',
            'address' : virtue['address']}).run(self.rethinkdb_manager.connection).next()

        destination_valor = self.rethinkdb_manager.get_valor(destination_valor_id)

        if current_valor['valor_id'] == destination_valor_id:
            raise Exception(('ERROR: Source valor [{0}] and Destination Valor [{1}] '
                             'are the same'.format(current_valor['valor_id'],
                                                   destination_valor_id)))

        virtues_on_dst_valor = rethinkdb.db('transducers').table('galahad').filter({
            'function': 'virtue',
            'address': destination_valor['address']}).run(self.rethinkdb_manager.connection)

        dst_virtue_count = len(list(virtues_on_dst_valor))
        if (dst_virtue_count >= MAX_VIRTUES_PER_VALOR):
            raise Exception(('ERROR: Destination Valor has too many ({0})'
                             ' Virtues running on it'
                             ' to migrate.'.format(dst_virtue_count)))

        rethinkdb.db("transducers").table("commands") \
            .filter({'valor_ip': current_valor['address'],
                     'virtue_id': virtue_id}) \
            .update({'valor_dest': destination_valor['address'],
                     'enabled': True}).run(self.rethinkdb_manager.connection)

        rethinkdb.db('transducers').table('commands') \
            .filter({'virtue_id': virtue_id,
                     'transducer_id': 'introspection'}) \
            .update({"valor_id": destination_valor_id}).run(self.rethinkdb_manager.connection)


    def add_virtue(self, valor_address, valor_id, virtue_id, efs_path, role_create=False):
        self.create_standby_valors()

        return self.rethinkdb_manager.add_virtue(valor_address, valor_id, virtue_id,
                                                 efs_path, role_create)

    def list_virtues(self):
        return self.rethinkdb_manager.list_virtues()


    def auto_migration_start(self, migration_interval):
        self.rethinkdb_manager.auto_migration_start(migration_interval)

    def auto_migration_stop(self):
        self.rethinkdb_manager.auto_migration_stop()

    def auto_migration_status(self):
        return self.rethinkdb_manager.auto_migration_status()

    def is_auto_migration_on(self):
        return self.rethinkdb_manager.is_auto_migration_on()

class RethinkDbManager:

    domain_name = 'rethinkdb.galahad.com'

    def __init__(self):

        try:
            self.connection = rethinkdb.connect(
                host = self.domain_name,
                port = 28015,
                ssl = {
                    'ca_certs':'/var/private/ssl/rethinkdb_cert.pem',
                })

        except Exception as error:
            print(error)
            raise Exception('ERROR: Failed to connect to RethinkDB: {}'.format(error))


    def get_valor(self, valor_id):

        response = rethinkdb.db('transducers').table('galahad').filter(
            {'function': 'valor', 'valor_id': valor_id}).run(self.connection)

        valor = list(response.items)

        # Return the first item in the list as there should only be 1 valor entry
        # corresponding to the specified valor_id
        if (len(valor) == 0):
            return None

        return valor[0]

    def set_valor(self, valor_id, key, value):

        valor_query = rethinkdb.db('transducers').table('galahad').filter(
            {'function': 'valor', 'valor_id': valor_id})

        valor_query.update({key: value}).run(self.connection)

        return self.get_valor(valor_id)

    def list_valors(self):

        response = rethinkdb.db('transducers').table('galahad').filter(
            {'function' : 'valor'}).run(self.connection)

        valors = list(response.items)

        # Remove the rethinkdb generated "id" field as it is not relevant.
        for valor in valors:
            valor.pop('id', None)

        return valors


    def list_virtues(self):

        response = rethinkdb.db('transducers').table('galahad').filter(
            {'function' : 'virtue'}).run(self.connection)

        virtues = list(response.items)

        return virtues


    def add_valor(self, valor):

        assert valor.guestnet == None

        lock.acquire()

        try:
            valor.guestnet = self.get_free_guestnet()

            record = {
                'function': 'valor',
                'guestnet': valor.guestnet,
                'valor_id': valor.aws_instance.id,
                'address' : valor.aws_instance.private_ip_address,
                'state'   : 'CREATING'
            }

            rethinkdb.db('transducers').table('galahad').insert([record]).run(
                self.connection)
        finally:
            lock.release()


    def remove_valor(self, valor_id):

        matching_valors = list(
            rethinkdb.db('transducers').table('galahad').filter({
                'function': 'valor',
                'valor_id': valor_id}).run(self.connection))

        rethinkdb.db('transducers').table('galahad').filter(
            matching_valors[0]).delete().run(self.connection)


    def get_free_guestnet(self):

        guestnet = '10.91.0.{0}'

        for test_number in range(1, 256):
            results = rethinkdb.db('transducers').table('galahad').filter({
                'guestnet': guestnet.format(test_number)}).run(self.connection)
            if len(list(results)) == 0:
                guestnet = guestnet.format(test_number)
                break

        # If this fails, then there was no available guestnet
        assert '{0}' not in guestnet

        return guestnet


    def add_virtue(self, valor_address, valor_id, virtue_id, efs_path, role_create):

        matching_virtues = list(rethinkdb.db('transducers').table('galahad').filter({
            'function': 'virtue',
            'virtue_id': virtue_id
        }).run(self.connection))

        assert len(matching_virtues) == 0

        lock.acquire()

        try:
            guestnet = self.get_free_guestnet()

            record = {
                'function' : 'virtue',
                'virtue_id': virtue_id,
                'valor_id' : valor_id,
                'address'  : valor_address,
                'guestnet' : guestnet,
                'img_path' : efs_path
            }
            rethinkdb.db('transducers').table('galahad').insert([record]).run(
                self.connection)
        finally:
            lock.release()

        if not role_create:

            # Calling next() on an empty cursor will error out
            try:
                trans_migration = rethinkdb.db('transducers').table('commands')\
                   .filter({'virtue_id': virtue_id, 'transducer_id': 'migration'}).run(self.connection).next()
            except:
                trans_migration = {} 

            try:
                trans_introspection = rethinkdb.db('transducers').table('commands')\
                    .filter({'virtue_id': virtue_id, 'transducer_id': 'introspection'}).run(self.connection).next()
            except:
                trans_introspection = {}

            trans_migration['valor_ip'] = valor_address
            trans_migration['valor_dest'] = None
            trans_migration['history'] = []
            rethinkdb.db('transducers').table('commands').filter({'virtue_id': virtue_id,
                'transducer_id': 'migration'}).update(trans_migration).run(self.connection)

            trans_introspection['valor_id'] = valor_id
            trans_introspection['interval'] = 10
            trans_introspection['comms'] = []
            rethinkdb.db('transducers').table('commands').filter({'virtue_id': virtue_id,
                'transducer_id': 'introspection'}).update(trans_introspection).run(self.connection)

        return guestnet


    def get_virtue(self, virtue_id):

        matching_virtues = list(rethinkdb.db('transducers').table('galahad').filter({
            'function': 'virtue',
            'virtue_id': virtue_id
        }).run(self.connection))

        if len(matching_virtues) == 0:
            return None

        return matching_virtues[0]

    # Run on virtue stop and virtue destroy
    def remove_virtue(self, virtue_id):

        matching_virtues = list(rethinkdb.db('transducers').table('galahad').filter({
            'function': 'virtue',
            'virtue_id': virtue_id
        }).run(self.connection))

        assert len(matching_virtues) == 1

        rethinkdb.db('transducers').table('galahad').filter(
            matching_virtues[0]).delete().run(self.connection)

    # Run on only virtue destroy
    def destroy_virtue(self, virtue_id):
        rethinkdb.db('transducers').table('commands').filter(
            {'virtue_id', virtue_id}).delete().run(self.connection)
        rethinkdb.db('transducers').table('acks').filter(
            {'virtue_id', virtue_id}).delete().run(self.connection)

    def auto_migration_start(self, migration_interval):
        response = list(rethinkdb.db('transducers').table('galahad').filter(
            {'function': 'auto_migration'}).run(self.connection))
        if len(response) != 0:
            rethinkdb.db('transducers').table('galahad').filter(
                {'function': 'auto_migration'}).update(
                {'enabled': True, 'migration_interval': migration_interval}).run(self.connection)
        else:
            rethinkdb.db('transducers').table('galahad').insert(
                {'function': 'auto_migration', 'migration_interval': migration_interval,
                 'enabled': True}).run(self.connection)

    def auto_migration_stop(self):
        response = list(rethinkdb.db('transducers').table('galahad').filter(
            {'function': 'auto_migration'}).run(self.connection))
        if len(response) != 0:
            rethinkdb.db('transducers').table('galahad').filter(
                {'function': 'auto_migration'}).update(
                {'enabled': False, 'migration_interval': None}).run(self.connection)

    def auto_migration_status(self):
        response = list(rethinkdb.db('transducers').table('galahad').filter(
            {'function': 'auto_migration'}).run(self.connection))
        if len(response) != 0:
            return response[0].get('enabled', False), response[0].get(
                'migration_interval')
        else:
            return False, None

    def is_auto_migration_on(self):
        return self.auto_migration_status()[0]

    def introspect_virtue_start(self, virtue_id, interval, modules):
        rethink_filter = rethinkdb.db('transducers').table('commands').filter({
            'transducer_id': 'introspection', 'virtue_id': virtue_id})

        update_dict = {'enabled': True}

        if interval is not None: update_dict['interval'] = int(interval)
        if modules is not None: update_dict['comms'] = modules.split(',')

        rethink_filter.update(update_dict).run(self.connection)


    def introspect_virtue_stop(self, virtue_id):
        rethinkdb.db('transducers').table('commands').filter({
            'transducer_id': 'introspection', 'virtue_id': virtue_id}).update({'enabled': False}).run(self.connection)


    def get_router(self):

        router = list(rethinkdb.db('transducers').table('galahad').filter({
            'function': 'router'}).run(self.connection))

        if (len(router) == 0):
            return None

        return router[0]


class RouterManager:

    def __init__(self, router_ip):

        self.ip_address = router_ip
        self.client = None

    def add_valor(self, valor):
        # Call into router to add port to ovs bridge for the
        # valor being added to the system

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
                   '/user-keys/default-virtue-key.pem')

        if not self.client.check_access():
            print('ERROR: Failed to connect to valor with IP {} using SSH'.format(
                self.ip_address))
            raise Exception(
                'ERROR: Failed to connect to valor with IP {} using SSH'.format(self.ip_address))

class ResourceManager:
    def __init__(self, username, resource):
        self.username = username
        self.resource = resource

    def drive(self, virtue_ip, key_path, appIds):
        # map resource
        # map to different directory than /home/virtue - causing key error
        print("drive")

        for appId in appIds:
            try:
                ssh = ssh_tool('virtue', virtue_ip, key_path)
                ssh.ssh(
                    ('sudo mount.cifs {} /home/virtue/{}'
                     ' -o sec=krb5,user=VIRTUE\{}').format(
                         self.resource['unc'], appId, self.username))

            except Exception as e:
                print("Failed to mount shared drive on virtue with error: {}".format(e))

    def printer(self, virtue_ip, key_path, appIds):
        pass

    def email(self, virtue_ip, key_path, appIds):
        if not os.path.exists(os.path.join("/mnt/ost", self.username)):
            try:
                ret = subprocess.check_call("sudo mkdir -p /mnt/ost/{}".format(self.username), shell=True)
                assert ret == 0
                ret = subprocess.check_call("sudo chown nobody:nogroup /mnt/ost/{}".format(self.username), shell=True)
                assert ret == 0
            except Exception as e:
                print("Failed to create ost user directory with error: {}".format(e))
                return

        try:
            ssh = ssh_tool('virtue', virtue_ip, key_path)

            ssh.ssh('sudo mkdir /ost')

            ssh.ssh(('sudo mount -t nfs excalibur.galahad.com:/mnt/ost/{}'
                     ' /ost').format(self.username))
        except Exception as e:
            print("Failed to mount ost NFS directory on virtue with error: {}".format(e))

    def remove_drive(self, virtue_ip, key_path, appIds):
        for appId in appIds:
            try:
                ssh = ssh_tool('virtue', virtue_ip, key_path)
                ssh.ssh('sudo umount /home/virtue/{}'.format(appId))
            except Exception as e:
                print("Failed to unmount shared drive on virtue with error: {}".format(e))

    def remove_printer(self, virtue_ip, key_path, appIds):
        pass

    def remove_email(self, virtue_ip, key_path, appIds):
        ssh = ssh_tool('virtue', virtue_ip, key_path)
        ssh.ssh('sudo umount /ost')
        ssh.ssh('sudo rm -r /ost')
