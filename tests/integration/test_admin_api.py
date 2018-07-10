import os
import sys
import time
import json
import requests

from sso_login import sso_tool

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(file_path))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)
from website import ldap_tools
from website.ldaplookup import LDAP
from website.aws import AWS
from website.services.errorcodes import ErrorCodes

##
# Functionality of these API commands is tested by user/test_admin_api.py.
# These tests verify that the return values get into the https response correctly.
##


def setup_module():

    global session
    global base_url
    global inst

    with open('test_config.json', 'r') as infile:
        settings = json.load(infile)

    with open('../setup/excalibur_ip', 'r') as infile:
        ip = infile.read().strip() + ':' + settings['port']

    inst = LDAP( '', '' )
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s( dn, 'Test123!' )

    redirect = settings['redirect'].format(ip)

    sso = sso_tool(ip)
    assert sso.login(settings['user'], settings['password'])

    client_id = sso.get_app_client_id(settings['app_name'])
    if (client_id == None):
        client_id = sso.create_app(settings['app_name'], redirect)
        assert client_id

    code = sso.get_oauth_code(client_id, redirect)
    assert code

    token = sso.get_oauth_token(client_id, code, redirect)
    assert 'access_token' in token

    session = requests.Session()
    session.headers = {
        'Authorization': 'Bearer {0}'.format(token['access_token'])
    }
    session.verify = settings['verify']

    base_url = 'https://{0}/virtue/admin'.format(ip)


def test_application_list():

    response = session.get(base_url + '/application/list')
    ls = response.json()
    assert type(ls) == list
    for obj in ls:
        assert set(obj.keys()) == set(['id', 'name', 'version', 'os'])


def test_resource_get():

    # The error response when the api call's output can't be used is from the
    #   user error codes.
    response = session.get(base_url + '/resource/get')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/resource/get', params={'resourceId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.admin['invalidId']['result']


def test_resource_list():

    response = session.get(base_url + '/resource/list')
    ls = response.json()
    assert type(ls) == list
    for obj in ls:
        assert set(obj.keys()) == set(['id', 'type', 'unc', 'credentials'])


def test_resource_attach():

    response = session.get(base_url + '/resource/attach')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/resource/attach',
        params={
            'resourceId': 'DoesNotExist',
            'virtueId': 'DoesNotExist'
        })
    assert (response.json() == ErrorCodes.admin['invalidResourceId']['result']
            or
            response.json() == ErrorCodes.admin['invalidVirtueId']['result'])


def test_resource_detach():

    response = session.get(base_url + '/resource/detach')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/resource/detach',
        params={
            'resourceId': 'DoesNotExist',
            'virtueId': 'DoesNotExist'
        })
    assert (response.json() == ErrorCodes.admin['invalidResourceId']['result']
            or
            response.json() == ErrorCodes.admin['invalidVirtueId']['result'])


def test_role_create():

    response = session.get(base_url + '/role/create')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    role = {
        'name': 'TestRole',
        'version': '1.0',
        'applicationIds': [],
        'startingResourceIds': [],
        'startingTransducerIds': []
    }

    response = session.get(
        base_url + '/role/create',
        params={'role': json.dumps(role)}
    )
    print(response.json())
    assert set(response.json().keys()) == set(['id', 'name'])

    role_id = response.json()['id']

    role = inst.get_obj('cid', role_id, objectClass='OpenLDAProle', throw_error=True)
    assert role != ()
    ldap_tools.parse_ldap(role)
    assert role['amiId'][0:4] == 'ami-'

    test_virtue = inst.get_obj('croleId', role_id,
                               objectClass='OpenLDAPvirtue', throw_error=True)

    i = 0
    while (test_virtue == () and i < 60):
        time.sleep(1)
        test_virtue = inst.get_obj(
            'croleId', role_id, objectClass='OpenLDAPvirtue', throw_error=True
        )
        i = i + 1
    assert test_virtue != ()

    ldap_tools.parse_ldap(test_virtue)
    assert test_virtue['username'] == 'NULL'
    assert test_virtue['applicationIds'] == []
    assert test_virtue['awsInstanceId'][0:2] == 'i-'

    aws = AWS()
    test_virtue = aws.populate_virtue_dict(test_virtue)
    assert test_virtue['state'] in aws.aws_state_to_virtue_state.values()
    aws.instance_destroy(test_virtue['awsInstanceId'], block=False)


def test_role_list():

    response = session.get(base_url + '/role/list')
    ls = response.json()
    assert type(ls) == list
    for obj in ls:
        assert set(obj.keys()) == set([
            'id', 'name', 'version', 'applicationIds', 'startingResourceIds',
            'startingTransducerIds'
        ])


def test_system_export():

    response = session.get(base_url + '/system/export')
    assert response.json() == ErrorCodes.admin['notImplemented']['result']


def test_system_import():

    response = session.get(base_url + '/system/import')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/system/import', params={'data': 'DoesNotExist'})
    assert response.json() == ErrorCodes.admin['notImplemented']['result']


def test_test_import_user():

    response = session.get(base_url + '/test/import/user')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/test/import/user', params={'which': 'DoesNotExist'})
    assert response.json() == ErrorCodes.admin['notImplemented']['result']


def test_test_import_application():

    response = session.get(base_url + '/test/import/application')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/test/import/application',
        params={'which': 'DoesNotExist'})
    assert response.json() == ErrorCodes.admin['notImplemented']['result']


def test_test_import_role():

    response = session.get(base_url + '/test/import/role')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/test/import/role', params={'which': 'DoesNotExist'})
    assert response.json() == ErrorCodes.admin['notImplemented']['result']


def test_user_list():

    response = session.get(base_url + '/user/list')
    ls = response.json()
    assert type(ls) == list
    for obj in ls:
        assert set(obj.keys()) == set(['username', 'authorizedRoleIds'])


def test_user_get():

    response = session.get(base_url + '/user/get')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/user/get', params={'username': 'DoesNotExist'})
    assert response.json() == ErrorCodes.admin['invalidUsername']['result']


def test_user_virtue_list():

    response = session.get(base_url + '/user/virtue/list')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/user/virtue/list', params={'username': 'DoesNotExist'})
    assert response.json() == ErrorCodes.admin['invalidUsername']['result']


def test_user_role_authorize():

    response = session.get(base_url + '/user/role/authorize')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/user/get',
        params={
            'username': 'DoesNotExist',
            'roleId': 'DoesNotExist'
        })
    assert (response.json() == ErrorCodes.admin['invalidUsername']['result']
            or response.json() == ErrorCodes.admin['invalidRoleId']['result'])


def test_user_role_unauthorize():

    response = session.get(base_url + '/user/role/unauthorize')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/user/role/unauthorize',
        params={
            'username': 'DoesNotExist',
            'roleId': 'DoesNotExist'
        })
    assert (response.json() == ErrorCodes.admin['invalidUsername']['result']
            or response.json() == ErrorCodes.admin['invalidRoleId']['result'])
