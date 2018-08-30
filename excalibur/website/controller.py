import shutil
from ldaplookup import LDAP
import ldap_tools
from aws import AWS
import threading
import copy
import time
import botocore
import shlex
import subprocess
import os
from common import ssh_tool

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
    def __init__(self, ldap_user, ldap_password, role_id, user, role=None):
        super(CreateVirtueThread, self).__init__()

        self.inst = LDAP(ldap_user, ldap_password)

        self.role_id = role_id
        self.role = role

        self.username = user

    def run(self):

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
            'id': 'Virtue_{0}_{1}'.format(role['name'], int(time.time())),
            'username': self.username,
            'roleId': self.role_id,
            'applicationIds': [],
            'resourceIds': role['startingResourceIds'],
            'transducerIds': role['startingTransducerIds'],
            'state': 'CREATING',
            'ipAddress': 'NULL'
        }
        ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
        self.inst.add_obj(ldap_virtue, 'virtues', 'cid')

        virtue_path = '/mnt/efs/images/p_virtues/' + virtue['id'] + '.img'
        shutil.copy('/mnt/efs/images/non_p_virtues/' + role['id'] + '.img',
                    virtue_path)

        self.set_virtue_keys(virtue['id'], virtue_path)

        virtue['state'] = 'STOPPED'
        ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
        self.inst.add_obj(ldap_virtue, 'virtues', 'cid')

    def set_virtue_keys(self, virtue_id, virtue_path):
        # Local Dir for storing of keys, this will be replaced when key management is implemented
        key_dir = '{0}/galahad-keys'.format(os.environ['HOME'])

        # For now generate keys and store in local dir
        subprocess.check_output(shlex.split(
            ('ssh-keygen -t rsa -f {0}/{1}.pem '
             '-C "Virtue Key for {1}" -N ""').format(key_dir, virtue_id)))

        image_mount = '{0}/{1}'.format(os.environ['HOME'], virtue_id)
        os.mkdir(image_mount)

        try:
            subprocess.check_call(['mount',
                                   virtue_path,
                                   image_mount])

            with open(image_mount + '/etc/virtue-id', 'w') as id_file:
                id_file.write(virtue_id)

            if (not os.path.exists(image_mount + '/var/private/ssl')):
                os.makedirs(image_mount + '/var/private/ssl')

            shutil.copy('{0}/{1}.pem'.format(key_dir, virtue_id),
                        image_mount + '/var/private/ssl/virtue_1_key.pem')
            shutil.copy('{0}/{1}.pem'.format(key_dir, 'excalibur_pub'),
                        image_mount + '/var/private/ssl/excalibur_pub.pem')
            shutil.copy('{0}/{1}.pem'.format(key_dir, 'rethinkdb_cert'),
                        image_mount + '/var/private/ssl/rethinkdb_cert.pem')

            os.chown(image_mount + '/var/private', 501, 500)
            for path, dirs, files in os.walk(image_mount + '/var/private'):
                for f in files:
                    os.chown(os.path.join(path, f), 501, 500)
                    os.chmod(os.path.join(path, f), 0700)
                for d in dirs:
                    os.chown(os.path.join(path, d), 501, 500)
                    os.chmod(os.path.join(path, d), 0700)

            subprocess.check_call(['chroot', image_mount,
                                   'sed', '-i', '.*rethinkdb.*/d', '/etc/hosts'])

            with open(image_mount + '/etc/hosts', 'a') as hosts_file:
                hosts_file.write('172.30.1.45 rethinkdb.galahad.com\n')
                hosts_file.write('172.30.1.46 elasticsearch.galahad.com\n')

            subprocess.check_call([
                'chroot', image_mount, 'sed', '-i',
                's/host:.*/host: elasticsearch.galahad.com/',
                '/etc/syslog-ng/elasticsearch.yml'])
            subprocess.check_call([
                'chroot', image_mount, 'sed', '-i',
                's!cluster-url.*!cluster-url\("https\:\/\/elasticsearch.galahad.com:9200"\)!',
                '/etc/syslog-ng/syslog-ng.conf'])

        except:
            raise
        finally:
            subprocess.call(['umount', image_mount])
            os.rmdir(image_mount)
