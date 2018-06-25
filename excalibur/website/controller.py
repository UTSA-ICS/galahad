from ldaplookup import LDAP
import ldap_tools
from aws import AWS
import threading
import copy
import time

# Keep X virtues waiting to be assigned to users. The time
# overhead of creating them dynamically would be too long.
BACKUP_VIRTUE_COUNT = 2

# Time between AWS polls in seconds
POLL_TIME = 300

thread_list = []

# Copy/Pasted from virtue.py
aws_state_to_virtue_state = {
    'pending': 'CREATING',
    'running': 'RUNNING',
    'shutting-down': 'DELETING',
    'terminated': 'STOPPED',
    'stopping': 'STOPPING',
    'stopped': 'STOPPED'
}


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
            roles_dict = {}

            for r in roles:
                ldap_tools.parse_ldap(r)
                roles_dict[r['id']] = 0

            virtues = self.inst.get_objs_of_type('OpenLDAPvirtue')

            ec2 = boto3.client('ec2')

            for v in virtues:
                ldap_tools.parse_ldap(v)
                if (v['roleId'] in roles_dict and v['username'] == 'NULL'):
                    roles_dict[v['roleId']] += 1

                aws_inst_id = AWS.get_id_from_ip(v['ipAddress'])
                if (aws_inst_id == None):
                    # Delete the LDAP entry
                    print('Virtue was not found on AWS: {0}.'.format(
                        v['ipAddress']))
                    #self.inst.del_obj( 'cid', v['id'], objectClass='OpenLDAPvirtue' )

                vm_state = ec2.describe_instances(InstanceIds=[aws_inst_id])[
                    'Reservations'][0]['Instances'][0]['State']['Name']

                if (aws_state_to_virtue_state[vm_state] != v['state']):
                    # Update LDAP's virtue object
                    print('Virtue state has changed: {0} {1} -> {2}'.format(
                        v['id'], v['state'],
                        aws_state_to_virtue_state[vm_state]))
                    v['state'] = aws_state_to_virtue_state[vm['State']['Name']]
                    ldap_v = ldap_tools.to_ldap(v)
                    #self.inst.modify_obj( 'cid', v['id'], ldap_v, objectClass='OpenLDAPvirtue' )

            for t in thread_list:
                if (not t.is_alive()):
                    del t
                    continue

                if (t.role_id in roles_dict):
                    roles_dict[t.role_id] += 1

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
        instance = aws.instance_create(
            image_id=role['amiId'],
            inst_type='t2.small',
            subnet_id='subnet-026ad3430d66940d7',
            key_name='starlab-virtue-te',
            tag_key='Project',
            tag_value='Virtue',
            sec_group='sg-0b3cb1d7da878eb68',
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
            'state': aws_state_to_virtue_state[instance.state['Name']],
            'ipAddress': instance.public_ip_address
        }

        ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')

        self.inst.add_obj(ldap_virtue, 'virtues', 'cid')
