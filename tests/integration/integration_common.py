import os
import sys
import time
import json
import requests
import boto3

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(file_path))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)
from website import ldap_tools
from website.apiendpoint import EndPoint
from website.apiendpoint_admin import EndPoint_Admin
from website.aws import AWS
from website.services.errorcodes import ErrorCodes
sys.path.insert(0, base_excalibur_dir + '/cli')
from sso_login import sso_tool

def create_new_virtue(inst, role_data, user):

    ep = EndPoint('jmitchell', 'Test123!')
    ep.inst = inst

    epa = EndPoint_Admin('jmitchell', 'Test123!')
    epa.inst = inst

    # Get number of virtues
    ldap_virtues = inst.get_objs_of_type('OpenLDAPvirtue')
    ldap_virtue_len = len(ldap_virtues)

    # role_create
    if ('amiId' in role_data.keys()):
        ami_id = role_data['amiId']
        del role_data['amiId']
        new_role = json.loads(epa.role_create(role_data, hard_code_ami=ami_id))
    else:
        new_role = json.loads(epa.role_create(role_data))

    assert new_role not in ErrorCodes.admin.values()

    # user_role_authorize
    ret = epa.user_role_authorize(user, new_role['id'])
    assert ret == json.dumps(ErrorCodes.admin['success'])

    # Wait for virtue
    while (len(ldap_virtues) == ldap_virtue_len):
        time.sleep(2)
        ldap_virtues = inst.get_objs_of_type('OpenLDAPvirtue')
    virtues = ldap_tools.parse_ldap_list(ldap_virtues)

    for v in virtues:
        if (v['roleId'] == new_role['id'] and v['username'] == 'NULL'):
            virtue = v

    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(virtue['awsInstanceId'])
    instance.load()
    instance.wait_until_stopped()

    time.sleep(20)

    # virtue_create
    user_virtue = json.loads(epa.virtue_create('jmitchell', new_role['id']))
    assert set(user_virtue.keys()) == set(['id', 'ipAddress'])

    # virtue_launch
    ep.virtue_launch('jmitchell', user_virtue['id'])

    return json.loads(ep.virtue_get('jmitchell', user_virtue['id']))
