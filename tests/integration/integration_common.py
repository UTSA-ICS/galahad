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

def create_new_virtue(inst, role_data, user, hard_code_path=None):

    ep = EndPoint('jmitchell', 'Test123!')
    ep.inst = inst

    epa = EndPoint_Admin('jmitchell', 'Test123!')
    epa.inst = inst

    # role_create
    if (hard_code_path != None):
        new_role = json.loads(epa.role_create(role_data,
                                              hard_code_path=hard_code_path))
    else:
        new_role = json.loads(epa.role_create(role_data))

    assert new_role not in ErrorCodes.admin.values()

    # user_role_authorize
    ret = epa.user_role_authorize(user, new_role['id'])
    assert ret == json.dumps(ErrorCodes.admin['success'])

    # Wait for role to create
    role = {'state': 'CREATING'}
    while (role['state'] == 'CREATING'):
        time.sleep(2)
        role = inst.get_obj('cid', new_role['id'], objectClass='OpenLDAPvirtue')
        ldap_tools.parse_ldap(role)

    # virtue_create
    user_virtue = json.loads(epa.virtue_create('jmitchell', new_role['id']))
    assert set(user_virtue.keys()) == set(['id', 'ipAddress'])

    # virtue_launch
    ep.virtue_launch('jmitchell', user_virtue['id'])

    return json.loads(ep.virtue_get('jmitchell', user_virtue['id']))
