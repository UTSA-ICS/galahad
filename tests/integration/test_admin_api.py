import datetime
import json
import os
import subprocess
import sys
import time

import requests

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(file_path))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)

from website import ldap_tools
from website.ldaplookup import LDAP
from website.services.errorcodes import ErrorCodes
sys.path.insert(0, base_excalibur_dir + '/cli')
from sso_login import sso_tool

# For ssh_tool.py
sys.path.insert(0, '..')
from ssh_tool import ssh_tool

EXCALIBUR_HOSTNAME = 'excalibur.galahad.com'
AGGREGATOR_HOSTNAME = 'aggregator.galahad.com'
ELASTIC_TIMEOUT = 120 # Timeout before assuming elasticsearch query tests are failures
SLEEP_TIME = 10 # Time to sleep

##
# Functionality of these API commands is tested by user/test_admin_api.py.
# These tests verify that the return values get into the https response correctly.
##


def setup_module():

    global settings
    global session
    global base_url
    global inst
    global aggregator_ssh

    with open('test_config.json', 'r') as infile:
        settings = json.load(infile)

    with open('../aws_instance_info.json', 'r') as infile:
        tmp = json.load(infile)
        settings['subnet'] = tmp['subnet_id']
        settings['sec_group'] = tmp['sec_group']

    ip = EXCALIBUR_HOSTNAME + ':' + settings['port']

    aggregator_ip = AGGREGATOR_HOSTNAME

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

    subprocess.call(['sudo', 'mkdir', '-p', '/mnt/efs/images/tests'])
    subprocess.check_call(['sudo', 'rsync', '/mnt/efs/images/unities/4GB.img',
                           '/mnt/efs/images/tests/4GB.img'])

    aggregator_ssh = ssh_tool('ubuntu', aggregator_ip, sshkey='~/default-user-key.pem')


def __get_excalibur_index():
    # A new index is created every day
    now = datetime.datetime.now()
    index = now.strftime('excalibur-%Y.%m.%d')
    return index

def __query_elasticsearch_excalibur(args):
    assert aggregator_ssh.check_access()  # This prevents the result from being "added to know host" result from failing tests
    time.sleep(SLEEP_TIME) # Sleep to ensure logs make it to elasticsearch
    index = __get_excalibur_index()
    cmdargs = ''
    for (key, value) in args:
        cmdargs += '&q=' + str(key) + ':' + str(value)
    cmd = 'curl -s -X GET --insecure "https://admin:admin@localhost:9200/%s/_search?size=1&pretty%s"' % (index, cmdargs)
    output = aggregator_ssh.ssh(cmd, output=True)
    return json.loads(output)

# Elasticsearch is not meant for immediate retrevial of data, so we need to give a long timeout buffer
# to ensure tests don't fail due to logs not being available yet.  To not cause every test to take
# minutes, we query every SLEEP_TIME and stop at ELASTIC_TIMEOUT, or if we get a result.
def query_elasticsearch_with_timeout(args):
    elasped_time = 0
    while elasped_time < ELASTIC_TIMEOUT:
        result = __query_elasticsearch_excalibur(args)
        if 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0:
            return result
        elasped_time += SLEEP_TIME
    return result # Return last result, this will fail tests

def test_application_list():

    response = session.get(base_url + '/application/list')
    ls = response.json()
    assert type(ls) == list
    for obj in ls:
        assert (set(obj.keys()) == set(['id', 'name', 'version', 'os']) or
                set(obj.keys()) == set(['id', 'name', 'version', 'os', 'port']))

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_application_list')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_resource_get():

    # The error response when the api call's output can't be used is from the
    #   user error codes.
    response = session.get(base_url + '/resource/get')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/resource/get', params={'resourceId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.admin['invalidId']['result']

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_resource_get'), ('resource_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_resource_list():

    response = session.get(base_url + '/resource/list')
    ls = response.json()
    assert type(ls) == list
    for obj in ls:
        assert set(obj.keys()) == set(['id', 'type', 'unc', 'credentials'])

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_resource_list')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


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

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_resource_attach'),
         ('resource_id', 'DoesNotExist'), ('virtue_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


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

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_resource_detach'),
         ('resource_id', 'DoesNotExist'), ('virtue_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_role_create():

    response = session.get(base_url + '/role/create')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    role = {
        'name': 'TestRole',
        'version': '1.0',
        'applicationIds': ['firefox'],
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

    time.sleep(1)

    role = inst.get_obj('cid', role_id, objectClass='OpenLDAProle', throw_error=True)
    assert role != ()
    ldap_tools.parse_ldap(role)

    # TODO: Make sure loops like these don't continue forever.
    while (role['state'] == 'CREATING'):
        time.sleep(5)
        role = inst.get_obj('cid', role_id, objectClass='OpenLDAProle')
        ldap_tools.parse_ldap(role)

    assert role['state'] == 'CREATED'

    # TODO: Verify that the assembler has been run
    assert os.path.exists(('/mnt/efs/images/non_provisioned_virtues/'
                           '{0}.img').format(role['id']))

    inst.del_obj('cid', role['id'], objectClass='OpenLDAPvirtue',
                 throw_error=True)

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_role_create')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0

    subprocess.check_call(['sudo', 'rm',
                           ('/mnt/efs/images/non_provisioned_virtues/'
                            '{0}.img').format(role['id'])])


def test_role_list():

    response = session.get(base_url + '/role/list')
    ls = response.json()
    assert type(ls) == list
    for obj in ls:
        assert set(obj.keys()) == set([
            'id', 'name', 'version', 'applicationIds', 'startingResourceIds',
            'startingTransducerIds'
        ]) or set(obj.keys()) == set([
            'id', 'name', 'version', 'applicationIds', 'startingResourceIds',
            'startingTransducerIds', 'state'
        ])

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_role_list')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_system_export():

    response = session.get(base_url + '/system/export')
    assert response.json() == ErrorCodes.admin['notImplemented']['result']

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_application_list')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_system_import():

    response = session.get(base_url + '/system/import')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/system/import', params={'data': 'DoesNotExist'})
    assert response.json() == ErrorCodes.admin['notImplemented']['result']

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_application_list')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


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

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_user_list')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_user_get():

    response = session.get(base_url + '/user/get')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/user/get', params={'username': 'DoesNotExist'})
    assert response.json() == ErrorCodes.admin['invalidUsername']['result']

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_user_get'),
         ('requested_username', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_user_virtue_list():

    response = session.get(base_url + '/user/virtue/list')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/user/virtue/list', params={'username': 'DoesNotExist'})
    assert response.json() == ErrorCodes.admin['invalidUsername']['result']

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_user_virtue_list'),
         ('requested_username', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_user_role_authorize():

    response = session.get(base_url + '/user/role/authorize')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/user/role/authorize',
        params={
            'username': 'DoesNotExist',
            'roleId': 'DoesNotExist'
        })
    assert (response.json() == ErrorCodes.admin['invalidUsername']['result']
            or response.json() == ErrorCodes.admin['invalidRoleId']['result'])

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_user_role_authorize'),
         ('requested_username', 'DoesNotExist'), ('role_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


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

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_user_role_unauthorize'),
         ('requested_username', 'DoesNotExist'), ('role_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_virtue_create():

    response = session.get(base_url + '/virtue/create')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/virtue/create',
        params={
            'username': 'jmitchell',
            'roleId': 'DoesNotExist'
        })
    assert response.json() == ErrorCodes.admin['invalidRoleId']['result']

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'admin_virtue_create'),
         ('requested_username', 'DoesNotExist'), ('role_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_virtue_destroy():

    response = session.get(base_url + '/virtue/destroy')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    try:

        # 'Create' a Virtue
        subprocess.check_call(['sudo', 'mv', '/mnt/efs/images/tests/4GB.img',
                               ('/mnt/efs/images/provisioned_virtues/'
                               'TEST_VIRTUE_DESTROY.img')])

        virtue = {
            'id': 'TEST_VIRTUE_DESTROY',
            'username': 'jmitchell',
            'roleId': 'TBD',
            'applicationIds': [],
            'resourceIds': [],
            'transducerIds': [],
            'state': 'STOPPED',
            'ipAddress': 'NULL'
        }
        ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
        inst.add_obj(ldap_virtue, 'virtues', 'cid', throw_error=True)

        # virtue_destroy() it
        response = session.get(base_url + '/virtue/destroy',
                               params={'virtueId': 'TEST_VIRTUE_DESTROY'})
        assert response.text == json.dumps(ErrorCodes.admin['success'])

        assert not os.path.exists(('/mnt/efs/images/provisioned_virtues/'
                                   'TEST_VIRTUE_DESTROY.img'))

        assert () == inst.get_obj('cid', 'TEST_VIRTUE_DESTROY',
                                  objectClass='OpenLDAPvirtue',
                                  throw_error=True)


        result = query_elasticsearch_with_timeout(
            [('user', settings['user']), ('real_func_name', 'admin_virtue_destroy'),
             ('virtue_id', 'TEST_VIRTUE_DESTROY')])
        assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0

    except:
        raise
    finally:
        inst.del_obj('cid', 'TEST_VIRTUE_DESTROY', objectClass='OpenLDAPvirtue')
