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

def create_new_role(inst, role_data, hard_code_path=None):

    epa = EndPoint_Admin('jmitchell', 'Test123!')
    epa.inst = inst

    if (hard_code_path != None):
        new_role = json.loads(epa.role_create(role_data,
                                              hard_code_path=hard_code_path))
    else:
        new_role = json.loads(epa.role_create(role_data))

    assert new_role not in ErrorCodes.admin.values()

    time.sleep(5)

    # Wait for role to create
    role = {'state': 'CREATING'}
    while (role['state'] == 'CREATING'):
        time.sleep(2)
        role = inst.get_obj('cid', new_role['id'], objectClass='OpenLDAProle')
        ldap_tools.parse_ldap(role)

    return role

def create_new_virtue(inst, role_data, user, hard_code_path=None):

    ep = EndPoint('jmitchell', 'Test123!')
    ep.inst = inst

    epa = EndPoint_Admin('jmitchell', 'Test123!')
    epa.inst = inst

    roles = inst.get_objs_of_type('OpenLDAProle')
    roles = ldap_tools.parse_ldap_list(roles)

    test_role = None
    for role in roles:
        good_role = True
        for k in role_data:
            if role_data[k] != role.get(k):
                good_role = False
                break
        if good_role:
            test_role = role
            break

    if (test_role == None):
        test_role = create_new_role(inst, role_data,
                                    hard_code_path=hard_code_path)

    # user_role_authorize(). It's ok if the user is already authorized.
    epa.user_role_authorize(user, test_role['id'])

    # delete existing virtue if any
    user_virtue_list = json.loads(epa.user_virtue_list(user))
    for virtue in user_virtue_list:
        if (virtue['roleId'] == test_role['id']):
            ep.virtue_stop(user, virtue['id']) # It's ok if it's already stopped
            assert json.loads(epa.virtue_destroy(virtue['id'])) == \
                ErrorCodes.admin['success']

    # virtue_create()
    user_virtue = json.loads(epa.virtue_create(user, test_role['id']))
    assert set(user_virtue.keys()) == set(['id', 'ipAddress'])

    time.sleep(5)

    # Wait for virtue to create
    virtue = inst.get_obj('cid', user_virtue['id'],
                          objectClass='OpenLDAPvirtue')
    ldap_tools.parse_ldap(virtue)
    while (virtue['state'] == 'CREATING'):
        time.sleep(2)
        virtue = inst.get_obj('cid', virtue['id'], objectClass='OpenLDAPvirtue')
        ldap_tools.parse_ldap(virtue)
    assert virtue['state'] == 'STOPPED'

    # virtue_launch
    ep.virtue_launch(user, user_virtue['id'])

    return json.loads(ep.virtue_get(user, user_virtue['id']))
