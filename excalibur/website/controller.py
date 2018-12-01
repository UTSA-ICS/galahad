import os
import shlex
import subprocess
import threading
import time
import traceback

import ldap_tools
from aws import AWS
from ldaplookup import LDAP

from valor import ValorManager
from assembler.assembler import Assembler

# Keep X virtues waiting to be assigned to users. The time
# overhead of creating them dynamically would be too long.
BACKUP_VIRTUE_COUNT = 2

# Time between AWS polls in seconds
POLL_TIME = 300

thread_list = []


class BackgroundThread(threading.Thread):
    def __init__(self, ldap_user, ldap_password):
        super(BackgroundThread, self).__init__()

        self.inst = LDAP(ldap_user, ldap_password)
        # Going to need to write to LDAP
        #self.inst.bind_ldap()

        dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
        self.inst.get_ldap_connection()
        self.inst.conn.simple_bind_s(dn, 'Test123!')

        self.exit_requested = False

    def run(self):

        while (not self.exit_requested):

            # List all AWS instances

            roles = self.inst.get_objs_of_type('OpenLDAProle')
            roles = ldap_tools.parse_ldap_list(roles)

            for r in roles:
                backup_virtue_counts[r['id']] = 0

            virtues = self.inst.get_objs_of_type('OpenLDAPvirtue')
            virtues = ldap_tools.parse_ldap_list(virtues)

            aws = AWS()

            for v in virtues:

                if (v['roleId'] in roles_dict and v['username'] == 'NULL'):
                    roles_dict[v['roleId']] += 1

                v = aws.populate_virtue_dict(v)
                if (v['state'] == 'NULL' and v['awsInstanceId'] != 'NULL'):
                    # Delete the LDAP entry
                    print('Virtue was not found on AWS: {0}.'.format(
                        v['awsInstanceId']))
                    #self.inst.del_obj( 'cid', v['id'], objectClass='OpenLDAPvirtue' )

            for t in thread_list:
                if (not t.is_alive()):
                    del t
                    continue

                if (t.role_id in backup_virtue_counts):
                    backup_virtue_counts[t.role_id] += 1

            for r in roles:
                if (roles_dict[r['id']] < BACKUP_VIRTUE_COUNT):
                    thr = CreateVirtueThread(
                        self.inst.email, self.inst.password, r['id'], role=r)
                    thr.start()

            time.sleep(POLL_TIME)


class CreateVirtueThread(threading.Thread):
    def __init__(self, ldap_user, ldap_password, role_id, user, virtue_id,
                 role=None):
        super(CreateVirtueThread, self).__init__()

        self.inst = LDAP(ldap_user, ldap_password)

        self.role_id = role_id
        self.role = role

        self.username = user
        self.virtue_id = virtue_id

    def run(self):

        # Local Dir for storing of keys, this will be replaced when key management is implemented
        key_dir = '{0}/galahad-keys'.format(os.environ['HOME'])

        thread_list.append(self)

        # Going to need to write to LDAP
        #self.inst.bind_ldap()
        dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
        self.inst.get_ldap_connection()
        self.inst.conn.simple_bind_s(dn, 'Test123!')

        if (self.role == None):
            role = self.inst.get_obj(
                'cid', self.role_id, objectClass='OpenLDAProle')
            if (role == () or role == None):
                return
            ldap_tools.parse_ldap(role)
        else:
            role = self.role

        virtue = {
            'id': self.virtue_id,
            'username': self.username,
            'roleId': self.role_id,
            'applicationIds': [],
            'resourceIds': role['startingResourceIds'],
            'transducerIds': role['startingTransducerIds'],
            'state': 'CREATING',
            'ipAddress': 'NULL'
        }
        ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
        assert self.inst.add_obj(ldap_virtue, 'virtues', 'cid') == 0

        virtue_path = 'images/provisioned_virtues/' + virtue['id'] + '.img'

        try:

            # For now generate keys and store in local dir
            subprocess.check_output(shlex.split(
                ('ssh-keygen -t rsa -f {0}/{1}.pem -C'
                 ' "Virtue Key for {1}" -N ""').format(key_dir, virtue['id'])))

            with open(key_dir + '/' + virtue['id'] + '.pem',
                      'r') as virtue_key_file:
                virtue_key = virtue_key_file.read().strip()
            with open(key_dir + '/excalibur_pub.pem',
                      'r') as excalibur_key_file:
                excalibur_key = excalibur_key_file.read().strip()
            with open(key_dir + '/rethinkdb_cert.pem',
                      'r') as rdb_cert_file:
                rdb_cert = rdb_cert_file.read().strip()

            subprocess.check_call(['sudo', 'python',
                                   os.environ['HOME'] + '/galahad/excalibur/' + \
                                   'call_provisioner.py',
                                   '-i', virtue['id'],
                                   '-b', '/mnt/efs/images/non_provisioned_virtues/' +
                                   role['id'] + '.img',
                                   '-o', '/mnt/efs/' + virtue_path,
                                   '-v', virtue_key,
                                   '-e', excalibur_key,
                                   '-r', rdb_cert])

            virtue['state'] = 'STOPPED'
            ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
            assert self.inst.modify_obj('cid', virtue['id'], ldap_virtue) == 0
        except:
            print('Error while creating Virtue for role {0}:\n{1}'.format(
                role['id'], traceback.format_exc()))
            assert self.inst.del_obj('cid', virtue['id'],
                                     objectClass='OpenLDAPvirtue',
                                     throw_error=True) == 0
            os.remove('{0}/{1}.pem'.format(key_dir, virtue['id']))
            os.remove('{0}/{1}.pem.pub'.format(key_dir, virtue['id']))
            os.remove('/mnt/efs/' + virtue_path)

class AssembleRoleThread(threading.Thread):

    def __init__(self, ldap_user, ldap_password, role,
                 base_img_path,
                 use_ssh=True):
        super(AssembleRoleThread, self).__init__()

        self.inst = LDAP(ldap_user, ldap_password)

        # Going to need to write to LDAP
        #self.inst.bind_ldap()
        dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
        self.inst.get_ldap_connection()
        self.inst.conn.simple_bind_s(dn, 'Test123!')

        self.role = role

        self.base_img_path = base_img_path
        self.use_ssh = use_ssh

    def run(self):

        self.role['state'] = 'CREATING'

        ldap_role = ldap_tools.to_ldap(self.role, 'OpenLDAProle')
        ret = self.inst.add_obj(ldap_role, 'roles', 'cid', throw_error=True)

        assert ret == 0

        virtue_path = 'images/non_provisioned_virtues/' + self.role['id'] + '.img'
        key_path = os.environ['HOME'] + '/galahad-keys/default-virtue-key.pem'

        valor_manager = ValorManager()

        try:
            subprocess.check_call(['sudo', 'rsync',
                                   '/mnt/efs/' + self.base_img_path,
                                   '/mnt/efs/' + virtue_path])

            if (self.use_ssh):
                # Launch by adding a 'virtue' to RethinkDB
                valor = valor_manager.get_empty_valor()
                virtue_ip = valor_manager.rethinkdb_manager.add_virtue(
                    valor['address'],
                    valor['id'],
                    self.role['id'],
                    virtue_path)

                time.sleep(5)

                # Get Docker login command
                docker_cmd = subprocess.check_output(shlex.split(
                    'aws ecr get-login --no-include-email --region us-east-2'))

                print('docker_cmd: ' + docker_cmd)

                # Run assembler
                assembler = Assembler(work_dir='{0}/.{1}_assembly'.format(
                    os.environ['HOME'],
                    self.role['id']))
                assembler.assemble_running_vm(self.role['applicationIds'],
                                              docker_cmd,
                                              key_path,
                                              virtue_ip)

            self.role['state'] = 'CREATED'
            ldap_role = ldap_tools.to_ldap(self.role, 'OpenLDAProle')
            ret = self.inst.modify_obj('cid', self.role['id'], ldap_role,
                                       objectClass='OpenLDAProle',
                                       throw_error=True)

            assert ret == 0

        except:
            print('Error while assembling role {0}:\n{1}'.format(
                self.role['id'],
                traceback.format_exc()))

            self.role['state'] = 'FAILED'
            ldap_role = ldap_tools.to_ldap(self.role, 'OpenLDAProle')
            ret = self.inst.modify_obj('cid', self.role['id'], ldap_role,
                                       objectClass='OpenLDAProle',
                                       throw_error=True)
        finally:
            if valor_manager.rethinkdb_manager.get_virtue(self.role['id']):
                valor_manager.rethinkdb_manager.remove_virtue(self.role['id'])
