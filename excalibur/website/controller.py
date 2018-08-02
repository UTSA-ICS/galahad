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
    def __init__(self, ldap_user, ldap_password, role_id, role=None):
        super(CreateVirtueThread, self).__init__()

        self.inst = LDAP(ldap_user, ldap_password)

        self.role_id = role_id
        self.role = role

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

        # Create by calling AWS
        aws = AWS()
        ip = '{0}/32'.format(aws.get_public_ip())
        subnet = aws.get_subnet_id()
        sec_group = aws.get_sec_group()

        try:
            # Allow SSH from excalibur node
            sec_group.authorize_ingress(
                CidrIp=ip,
                FromPort=22,
                IpProtocol='tcp',
                ToPort=22
            )
        except botocore.exceptions.ClientError:
            print('ClientError encountered while adding sec group rule. ' +
                  'Rule probably exists already.')
        try:
            # TODO:
            # This is for testing and needs to be moved into cloud formation or env setup.
            # List of current allowable cidrs
            canvas_client_cidr = '70.121.205.81/32 172.3.30.184/32 35.170.157.4/32 129.115.2.249/32'
            for cidr in canvas_client_cidr.split():
                sec_group.authorize_ingress(
                    CidrIp=cidr,
                    FromPort=6761,
                    IpProtocol='tcp',
                    ToPort=6771
                )
        except botocore.exceptions.ClientError:
            print('ClientError encountered while adding sec group rule. ' +
                  'Rule probably exists already.')

        instance = aws.instance_create(
            image_id=role['amiId'],
            inst_type='t2.small',
            subnet_id=subnet,
            key_name='starlab-virtue-te',
            tag_key='Project',
            tag_value='Virtue',
            sec_group=sec_group.id,
            inst_profile_name='',
            inst_profile_arn='')


        instance.stop()
        instance.wait_until_stopped()
        instance.reload()

        virtue = {
            'id': 'Virtue_{0}_{1}'.format(role['name'], int(time.time())),
            'username': 'NULL',
            'roleId': self.role_id,
            'applicationIds': [],
            'resourceIds': role['startingResourceIds'],
            'transducerIds': role['startingTransducerIds'],
            'awsInstanceId': instance.id
        }
        ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
        self.inst.add_obj(ldap_virtue, 'virtues', 'cid')

        self.set_virtue_keys(virtue['id'], instance.public_ip_address)

    def check_virtue_access(self, ssh_inst):
        # Check if the virtue is accessible:
        for i in range(10):
            out = ssh_inst.ssh('uname -a', option='ConnectTimeout=10')
            if out == 255:
                time.sleep(30)
            else:
                print('Successfully connected to {}'.format(ssh_inst.ip))
                result = True
                return result
        if result != True:
            return False

    def set_virtue_keys(self, virtue_id, instance_ip):
        # Local Dir for storing of keys, this will be replaced when key management is implemented
        key_dir = '{0}/galahad-keys'.format(os.environ['HOME'])

        # For now generate keys and store in local dir
        subprocess.check_output(shlex.split(
                     'ssh-keygen -t rsa -f {0}/{1}.pem -C "Virtue Key for {1}" -N ""'.format(key_dir, virtue_id)))

        ssh_inst = ssh_tool('ubuntu', instance_ip, '{0}/default-virtue-key.pem'.format(key_dir))
        # Check if virtue is accessible.
        result = self.check_virtue_access(ssh_inst)

        if result == True:
            # Populate a virtue ID
            ssh_inst.ssh('sudo su - root -c "echo {0} > /etc/virtue-id"'.format(virtue_id))
            # Now populate virtue Merlin Dir with this key.
            ssh_inst.scp_to('{0}/{1}.pem'.format(key_dir, virtue_id), '/tmp/')
            ssh_inst.scp_to('{0}/{1}.pem'.format(key_dir, 'excalibur_pub'), '/tmp/')
            ssh_inst.scp_to('{0}/{1}.pem'.format(key_dir, 'rethinkdb_cert'), '/tmp/')
            #
            ssh_inst.ssh('sudo mv /tmp/{0}.pem /var/private/ssl/virtue_1_key.pem'.format(virtue_id))
            ssh_inst.ssh('sudo mv /tmp/{0}.pem /var/private/ssl/{0}.pem'.format('excalibur_pub'))
            ssh_inst.ssh('sudo mv /tmp/{0}.pem /var/private/ssl/{0}.pem'.format('rethinkdb_cert'))
            #
            ssh_inst.ssh('sudo chmod -R 700 /var/private;sudo chown -R merlin.virtue /var/private/')
            ssh_inst.ssh('sudo sed -i \'/.*rethinkdb.*/d\' /etc/hosts')
            ssh_inst.ssh('sudo su - root -c "echo 172.30.1.45 rethinkdb.galahad.com >> /etc/hosts"')
            ssh_inst.ssh('sudo su - root -c "echo 172.30.1.46 elasticsearch.galahad.com >> /etc/hosts"')
            ssh_inst.ssh('sudo sed -i \'s/host:.*/host: elasticsearch.galahad.com/\' /etc/syslog-ng/elasticsearch.yml')
            ssh_inst.ssh('sudo sed -i \'s!cluster-url.*!cluster-url\("https\:\/\/elasticsearch.galahad.com:9200"\)!\' /etc/syslog-ng/syslog-ng.conf')
            ssh_inst.ssh('sudo systemctl restart merlin')
            ssh_inst.ssh('sudo systemctl restart syslog-ng')
        else:
            raise Exception("Error accessing the Virtue with ID {0} and IP {1}".format(virtue_id, instance_ip))
