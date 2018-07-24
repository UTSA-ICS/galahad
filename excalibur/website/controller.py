from ldaplookup import LDAP
import ldap_tools
from aws import AWS
import threading
import copy
import time
import botocore

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
            # List of current cidrs
            # TODO:
            # This is for testing and needs to be moved into cloud formation or env setup.
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
        #instance = {'id': 'id_of_aws_inst', 'state': 'state_of_aws_inst', 'ip': '10.20.30.40'}

        instance.stop()
        instance.wait_until_stopped()
        instance.reload()

        virtue = {
            'id': 'Virtue_{0}{1}'.format(role['name'], int(time.time())),
            'username': 'NULL',
            'roleId': self.role_id,
            'applicationIds': [],
            'resourceIds': role['startingResourceIds'],
            'transducerIds': role['startingTransducerIds'],
            'awsInstanceId': instance.id
        }

        ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')

        self.inst.add_obj(ldap_virtue, 'virtues', 'cid')
