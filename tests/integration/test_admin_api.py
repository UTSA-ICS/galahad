import os
import sys
import json
import requests

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(os.path.dirname(os.path.dirname(file_path))) + '/flask-authlib'
sys.path.insert(0, base_excalibur_dir)
from website.services.errorcodes import ErrorCodes

##
# Functionality of these API commands is tested by user/test_admin_api.py.
# These tests verify that the return values get into the https response correctly.
##

def setup_module():

    global settings
    global token_data
    global session
    global base_url

    with open('test_config.json', 'r') as infile:
        settings = json.load(infile)

    # Need to get admin token eventually
    with open('token_data.json', 'r') as infile:
        token_data = json.load(infile)

    session = requests.Session()
    session.headers = {'Authorization':
                       'Bearer {0}'.format(token_data['access_token'])}
    session.verify = settings['verify']

    base_url = 'https://{0}/virtue/admin'.format(settings['ip'])

def test_application_list():

    res = session.get(base_url + '/application/list')
    ls = res.json()
    assert type(ls) == list
    for obj in ls:
        assert 'id' in obj
        assert 'name' in obj
        assert 'os' in obj

def test_resource_get():

    # The error response when the api call's output can't be used is from the
    #   user error codes.
    res = session.get(base_url + '/resource/get')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/resource/get',
                      params={'resourceId': 'DoesNotExist'})
    assert res.json() == ErrorCodes.admin['invalidId']['result']

def test_resource_list():

    res = session.get(base_url + '/resource/list')
    ls = res.json()
    assert type(ls) == list
    for obj in ls:
        assert 'id' in obj
        assert 'unc' in obj

def test_resource_attach():

    res = session.get(base_url + '/resource/attach')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/resource/attach',
                      params={'resourceId': 'DoesNotExist',
                              'virtueId': 'DoesNotExist'})
    assert (res.json() == ErrorCodes.admin['invalidResourceId']['result']
            or res.json() == ErrorCodes.admin['invalidVirtueId']['result'])

def test_resource_detach():

    res = session.get(base_url + '/resource/detach')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/resource/detach',
                      params={'resourceId': 'DoesNotExist',
                              'virtueId': 'DoesNotExist'})
    assert (res.json() == ErrorCodes.admin['invalidResourceId']['result']
            or res.json() == ErrorCodes.admin['invalidVirtueId']['result'])

def test_role_create():

    res = session.get(base_url + '/role/create')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/role/create',
                      params={
                          'role': json.dumps({
                              'name': 'BadRole',
                              'version': '42'
                          })
                      })
    assert res.json() == ErrorCodes.admin['invalidFormat']['result']

def test_role_list():

    res = session.get(base_url + '/role/list')
    ls = res.json()
    assert type(ls) == list
    for obj in ls:
        assert 'id' in obj
        assert 'name' in obj
        assert 'startingResourceIds' in obj

def test_system_export():

    res = session.get(base_url + '/system/export')
    assert res.json() == ErrorCodes.admin['notImplemented']['result']

def test_system_import():

    res = session.get(base_url + '/system/import')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/system/import',
                      params={'data': 'DoesNotExist'})
    assert res.json() == ErrorCodes.admin['notImplemented']['result']

def test_test_import_user():

    res = session.get(base_url + '/test/import/user')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/test/import/user',
                      params={'which': 'DoesNotExist'})
    assert res.json() == ErrorCodes.admin['notImplemented']['result']

def test_test_import_application():

    res = session.get(base_url + '/test/import/application')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/test/import/application',
                      params={'which': 'DoesNotExist'})
    assert res.json() == ErrorCodes.admin['notImplemented']['result']

def test_test_import_role():

    res = session.get(base_url + '/test/import/role')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/test/import/role',
                      params={'which': 'DoesNotExist'})
    assert res.json() == ErrorCodes.admin['notImplemented']['result']

def test_user_list():

    res = session.get(base_url + '/user/list')
    ls = res.json()
    assert type(ls) == list
    for obj in ls:
        assert 'username' in obj
        assert 'authorizedRoleIds' in obj

def test_user_get():

    res = session.get(base_url + '/user/get')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/user/get',
                      params={'username': 'DoesNotExist'})
    assert res.json() == ErrorCodes.admin['invalidUsername']['result']

def test_user_virtue_list():

    res = session.get(base_url + '/user/virtue/list')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/user/virtue/list',
                      params={'username': 'DoesNotExist'})
    assert res.json() == ErrorCodes.admin['invalidUsername']['result']

def test_user_role_authorize():

    res = session.get(base_url + '/user/role/authorize')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/user/get',
                      params={'username': 'DoesNotExist',
                              'roleId': 'DoesNotExist'})
    assert (res.json() == ErrorCodes.admin['invalidUsername']['result']
            or res.json() == ErrorCodes.admin['invalidRoleId']['result'])

def test_user_role_unauthorize():

    res = session.get(base_url + '/user/role/unauthorize')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/user/role/unauthorize',
                      params={'username': 'DoesNotExist',
                              'roleId': 'DoesNotExist'})
    assert (res.json() == ErrorCodes.admin['invalidUsername']['result']
            or res.json() == ErrorCodes.admin['invalidRoleId']['result'])

