import datetime
import json
import os
import subprocess
import sys
import time

import pytest

import requests

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(file_path))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)
from website import ldap_tools
from website.ldaplookup import LDAP
from website.services.errorcodes import ErrorCodes
from website.valor import RethinkDbManager
sys.path.insert(0, base_excalibur_dir + '/cli')
from sso_login import sso_tool

# For ssh_tool.py
sys.path.insert(0, '..')
from ssh_tool import ssh_tool

key_path = os.environ['HOME'] + '/galahad-keys/default-virtue-key.pem'

EXCALIBUR_HOSTNAME = 'excalibur.galahad.com'
AGGREGATOR_HOSTNAME = 'aggregator.galahad.com'
ELASTIC_TIMEOUT = 120 # Timeout before assuming elasticsearch query tests are failures
SLEEP_TIME = 10 # Time to sleep

##
# Functionality of these API commands is tested by unit/test_user_api.py.
# These tests verify that the return values get into the https response correctly.
##


def setup_module():

    global settings
    global inst
    global session
    global ip
    global base_url
    global test_valor_id
    global aggregator_ssh

    with open('test_config.json', 'r') as infile:
        settings = json.load(infile)

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

    base_url = 'https://{0}/virtue/user'.format(ip)

    subprocess.call(['sudo', 'mkdir', '-p', '/mnt/efs/images/tests'])
    subprocess.check_call(['sudo', 'rsync', '/mnt/efs/images/unities/8GB.img',
                           '/mnt/efs/images/tests/8GB.img'])

    aggregator_ssh = ssh_tool('ubuntu', aggregator_ip, sshkey='~/default-user-key.pem')

def teardown_module():
    pass

def __get_excalibur_index():
    # A new index is created every day
    now = datetime.datetime.now()
    index = now.strftime('excalibur-%Y.%m.%d')
    return index

def __query_elasticsearch_excalibur(args):
    assert aggregator_ssh.check_access() # This prevents the result from being "added to know host" result from failing tests
    time.sleep(30) # Sleep to ensure logs make it to elasticsearch
    index = __get_excalibur_index()
    cmdargs = ''
    for (key, value) in args:
        cmdargs += '&q=' + str(key) + ':' + str(value)
    cmd = 'curl -s -X GET --insecure "https://admin:admin@localhost:9200/%s/_search?size=1&pretty%s"' % (index, cmdargs)
    output = aggregator_ssh.ssh(cmd, output=True)
    return json.loads(output)

def query_elasticsearch_with_timeout(args):
    elasped_time = 0
    while elasped_time < ELASTIC_TIMEOUT:
        result = __query_elasticsearch_excalibur(args)
        if 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0:
            return result
        elasped_time += SLEEP_TIME
    return result # Return last result, this will fail tests

def test_application_get():

    # Test error in excalibur by not giving an appId.
    response = session.get(base_url + '/application/get')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    # Test error in endpoint by giving valid data with a predictable response that
    # only comes from the api endpoint.
    response = session.get(
        base_url + '/application/get', params={'appId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.user['invalidId']['result']

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'application_get'), ('app_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_role_get():

    response = session.get(base_url + '/role/get')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/role/get', params={'roleId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.user['invalidId']['result']

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'role_get'), ('role_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_user_role_list():

    # Kind of hard to make this fail.
    response = session.get(base_url + '/role/list')
    ls = response.json()
    assert type(ls) == list
    for obj in ls:
        assert (set(obj.keys()) == set([
            'id', 'name', 'version', 'applicationIds', 'startingResourceIds',
            'startingTransducerIds', 'networkRules', 'ipAddress'
        ]) or set(obj.keys()) == set([
            'id', 'name', 'version', 'applicationIds', 'startingResourceIds',
            'startingTransducerIds', 'networkRules', 'ipAddress', 'state'
        ]))

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'user_role_list')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_user_virtue_list():

    # Kind of hard to make this fail.
    response = session.get(base_url + '/virtue/list')
    ls = response.json()
    assert type(ls) == list
    for obj in ls:
        assert set(obj.keys()) == set([
            'id', 'username', 'roleId', 'applicationIds', 'resourceIds',
            'transducerIds', 'networkRules', 'state', 'ipAddress'
        ])

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'user_virtue_list')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_virtue_get():

    response = session.get(base_url + '/virtue/get')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/virtue/get', params={'virtueId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.user['invalidId']['result']

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'virtue_get'), ('virtue_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_virtue_launch():

    response = session.get(base_url + '/virtue/launch')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    rethink_manager = RethinkDbManager()

    try:

        # 'Create' a Virtue
        subprocess.check_call(['sudo', 'mv', '/mnt/efs/images/tests/8GB.img',
                               ('/mnt/efs/images/provisioned_virtues/'
                                'TEST_VIRTUE_LAUNCH.img')])

        virtue = {
            'id': 'TEST_VIRTUE_LAUNCH',
            'username': 'slapd',
            'roleId': 'TBD',
            'applicationIds': [],
            'resourceIds': [],
            'transducerIds': [],
            'networkRules': [],
            'state': 'STOPPED',
            'ipAddress': 'NULL'
        }
        ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
        inst.add_obj(ldap_virtue, 'virtues', 'cid', throw_error=True)

        # virtue_launch() it
        response = session.get(base_url + '/virtue/launch',
                               params={'virtueId': 'TEST_VIRTUE_LAUNCH'})
        assert response.text == json.dumps(ErrorCodes.user['success'])

        real_virtue = inst.get_obj(
            'cid',
            'TEST_VIRTUE_LAUNCH',
            objectClass='OpenLDAPvirtue',
            throw_error=True)
        ldap_tools.parse_ldap(real_virtue)

        assert 'RUNNING' in real_virtue['state']

        rethink_virtue = rethink_manager.get_virtue('TEST_VIRTUE_LAUNCH')

        assert type(rethink_virtue) == dict

        rethink_valors = rethink_manager.list_valors()
        rethink_valor = None
        for valor in rethink_valors:
            if (valor['address'] == rethink_virtue['address']):
                rethink_valor = valor
                break

        assert rethink_valor != None

        sysctl_stat = subprocess.call(
            ['ssh', '-i', key_path, 'ubuntu@' + rethink_virtue['address'],
             '-o', 'StrictHostKeyChecking=no',
             'sudo systemctl status gaius'])

        # errno=3 means that gaius isn't running
        assert sysctl_stat == 0

        xl_list = subprocess.check_output(
            ['ssh', '-i', key_path, 'ubuntu@' + rethink_virtue['address'],
             '-o', 'StrictHostKeyChecking=no',
             'sudo xl list'])

        # There should be one VM running on the valor. If the test's virtue
        # isn't the only one that's running, this failure may be a false alarm.
        assert xl_list.count('\n') == 3

        response = session.get(base_url + '/virtue/launch',
                               params={'virtueId': 'TEST_VIRTUE_LAUNCH'})
        assert response.text == json.dumps(ErrorCodes.user['virtueAlreadyLaunched']['result'])

        result = query_elasticsearch_with_timeout(
            [('user', settings['user']), ('real_func_name', 'virtue_launch'),
             ('virtue_id', 'TEST_VIRTUE_LAUNCH')])
        assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0

    except:
        raise
    finally:
        inst.del_obj('cid', 'TEST_VIRTUE_LAUNCH', objectClass='OpenLDAPvirtue')
        subprocess.check_call(['sudo', 'mv',
                               ('/mnt/efs/images/provisioned_virtues/'
                                'TEST_VIRTUE_LAUNCH.img'),
                               '/mnt/efs/images/tests/8GB.img'])
        rethink_manager.remove_virtue('TEST_VIRTUE_LAUNCH')

def test_virtue_stop():

    response = session.get(base_url + '/virtue/stop')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    rethink_manager = RethinkDbManager()

    try:

        # 'Create' a Virtue
        subprocess.check_call(['sudo', 'mv', '/mnt/efs/images/tests/8GB.img',
                               ('/mnt/efs/images/provisioned_virtues/'
                                'TEST_VIRTUE_STOP.img')])

        virtue = {
            'id': 'TEST_VIRTUE_STOP',
            'username': 'slapd',
            'roleId': 'TBD',
            'applicationIds': [],
            'resourceIds': [],
            'transducerIds': [],
            'networkRules': [],
            'state': 'STOPPED',
            'ipAddress': 'NULL'
        }
        ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
        inst.add_obj(ldap_virtue, 'virtues', 'cid', throw_error=True)

        # virtue_launch() it
        response = session.get(base_url + '/virtue/launch',
                               params={'virtueId': 'TEST_VIRTUE_STOP'})
        assert response.text == json.dumps(ErrorCodes.user['success'])

        rethink_virtue = rethink_manager.get_virtue('TEST_VIRTUE_STOP')

        assert type(rethink_virtue) == dict

        # virtue_stop() it
        response = session.get(base_url + '/virtue/stop',
                               params={'virtueId': 'TEST_VIRTUE_STOP'})
        assert response.text == json.dumps(ErrorCodes.user['success'])

        time.sleep(5)

        real_virtue = inst.get_obj(
            'cid',
            'TEST_VIRTUE_STOP',
            objectClass='OpenLDAPvirtue',
            throw_error=True)
        ldap_tools.parse_ldap(real_virtue)

        assert real_virtue['state'] == 'STOPPED'

        assert rethink_manager.get_virtue('TEST_VIRTUE_STOP') == None

        sysctl_stat = subprocess.call(
            ['ssh', '-i', key_path, 'ubuntu@' + rethink_virtue['address'],
             '-o', 'StrictHostKeyChecking=no',
             'sudo systemctl status gaius'],
            stdout=subprocess.PIPE)

        # errno=3 means that gaius isn't running
        assert sysctl_stat == 0

        xl_list = subprocess.check_output(
            ['ssh', '-i', key_path, 'ubuntu@' + rethink_virtue['address'],
             '-o', 'StrictHostKeyChecking=no',
             'sudo xl list'])

        # There shouldn't be a VM running on the valor. If the test's virtue
        # isn't the only one that's running, this failure may be a false alarm.
        assert xl_list.count('\n') == 2

        response = session.get(base_url + '/virtue/stop',
                               params={'virtueId': 'TEST_VIRTUE_STOP'})
        assert response.text == json.dumps(ErrorCodes.user['virtueAlreadyStopped']['result'])

        result = query_elasticsearch_with_timeout(
            [('user', settings['user']), ('real_func_name', 'virtue_stop'),
             ('virtue_id', 'TEST_VIRTUE_STOP')])
        assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0

    except:
        raise
    finally:
        inst.del_obj('cid', 'TEST_VIRTUE_STOP', objectClass='OpenLDAPvirtue')
        subprocess.check_call(['sudo', 'mv',
                               ('/mnt/efs/images/provisioned_virtues/'
                                'TEST_VIRTUE_STOP.img'),
                               '/mnt/efs/images/tests/8GB.img'])


def test_virtue_application_launch():

    response = session.get(base_url + '/virtue/application/launch')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/virtue/application/launch',
        params={
            'virtueId': 'DoesNotExist',
            'appId': 'DoesNotExist'
        })
    assert (
        response.json() == ErrorCodes.user['invalidVirtueId']['result'] or
        response.json() == ErrorCodes.user['invalidApplicationId']['result'])

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'virtue_application_launch'),
         ('virtue_id', 'DoesNotExist'), ('app_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_virtue_application_stop():

    response = session.get(base_url + '/virtue/application/stop')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/virtue/application/stop',
        params={
            'virtueId': 'DoesNotExist',
            'appId': 'DoesNotExist'
        })
    assert (
        response.json() == ErrorCodes.user['invalidVirtueId']['result'] or
        response.json() == ErrorCodes.user['invalidApplicationId']['result'])

    result = query_elasticsearch_with_timeout(
        [('user', settings['user']), ('real_func_name', 'virtue_application_stop'),
         ('virtue_id', 'DoesNotExist'), ('app_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0
