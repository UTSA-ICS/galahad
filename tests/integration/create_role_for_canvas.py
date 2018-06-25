import os
import sys
import json
import time
import argparse
import boto3

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(file_path)) + '/../excalibur'
sys.path.insert(0, base_excalibur_dir)
from website import ldap_tools
from website.ldaplookup import LDAP
from website.apiendpoint import EndPoint
from website.apiendpoint_admin import EndPoint_Admin
from website.aws import AWS
from website.services.errorcodes import ErrorCodes


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-a',
        '--ami',
        type=str,
        required=True,
        help='The AMI ID to use'
    )
    parser.add_argument(
        '-n',
        '--name',
        type=str,
        required=True,
        help='The name to give the new role'
    )
    parser.add_argument(
        '--apps',
        type=str,
        nargs='*',
        required=True,
        help='The application IDs to add to the role'
    )

    args = parser.parse_args()
    return args


if (__name__ == '__main__'):

    args = parse_args()

    inst = LDAP('', '')
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s(dn, 'Test123!')

    ep = EndPoint('jmitchell', 'Test123!')
    ep.inst = inst

    epa = EndPoint_Admin('jmitchell', 'Test123!')
    epa.inst = inst

    role = {
        'name': args.name,
        'version': '1.0',
        'applicationIds': args.apps,
        'startingResourceIds': [],
        'startingTransducerIds': []
    }

    new_role = json.loads(epa.role_create(role, use_aws=True, hard_code_ami=args.ami))

    assert set(new_role.keys()) == set(['id', 'name'])

    ldap_virtues = inst.get_objs_of_type('OpenLDAPvirtue')
    ldap_virtue_len = len(ldap_virtues)

    role = inst.get_obj('cid', new_role['id'], objectClass='OpenLDAProle',
                        throw_error=True)
    assert role != ()
    ldap_tools.parse_ldap(role)

    ret = epa.user_role_authorize('jmitchell', role['id'])

    print(ret)

    assert ret == None #json.dumps(ErrorCodes.admin['success'])

    while (len(ldap_virtues) == ldap_virtue_len):
        time.sleep(1)
        ldap_virtues = inst.get_objs_of_type('OpenLDAPvirtue')
    virtues = ldap_tools.parse_ldap_list(ldap_virtues)

    for v in virtues:
        if (v['roleId'] == role['id'] and v['username'] == 'NULL'):
            virtue = v

    aws = AWS()
    inst_id = aws.get_id_from_ip(virtue['ipAddress'])

    assert inst_id != None

    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(inst_id)
    instance.load()
    assert instance.state['Name'] == 'stopped'

    instance.start()
    instance.wait_until_running()

    ldap_virtue = inst.get_obj('cid', virtue['id'], objectClass='OpenLDAPvirtue',
                               throw_error=True)
    ldap_virtue['cstate'] = 'RUNNING'
    inst.modify_obj('cid', virtue['id'], ldap_virtue,
                    objectClass='OpenLDAPvirtue', throw_error=True)

    user_virtue = json.loads(ep.virtue_create('jmitchell', role['id']))

    assert set(user_virtue.keys()) == set(['id', 'ipAddress'])

    print('Instance ID: {0}'.format(inst_id))

    
