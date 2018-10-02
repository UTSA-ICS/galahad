import os
import datetime
import sys
import json
import requests
import time

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(file_path))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)
from website import ldap_tools
from website.ldaplookup import LDAP
from website.services.errorcodes import ErrorCodes
from website.aws import AWS
sys.path.insert(0, base_excalibur_dir + '/cli')
from sso_login import sso_tool

# For common.py
sys.path.insert(0, '..')
from common import ssh_tool


##
# Functionality of these API commands is tested by unit/test_user_api.py.
# These tests verify that the return values get into the https response correctly.
##


def setup_module():

    global settings
    global inst
    global session
    global base_url
    global aggregator_ssh

    with open('test_config.json', 'r') as infile:
        settings = json.load(infile)

    with open('../setup/aws_instance_info.json', 'r') as infile:
        tmp = json.load(infile)
        settings['subnet'] = tmp['subnet_id']
        settings['sec_group'] = tmp['sec_group']

    with open('../setup/excalibur_ip', 'r') as infile:
        ip = infile.read().strip() + ':' + settings['port']

    aggregator_ip = None
    with open('../setup/aggregator_ip', 'r') as infile:
        aggregator_ip = infile.read().strip()

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

    aggregator_ssh = ssh_tool('ubuntu', aggregator_ip, sshkey='~/default-user-key.pem')



def __get_excalibur_index():
    # A new index is created every day
    now = datetime.datetime.now()
    index = now.strftime('excalibur-%Y.%m.%d')
    return index

def __query_elasticsearch_excalibur(args):
    time.sleep(10) # Sleep to ensure logs make it to elasticsearch
    index = __get_excalibur_index()
    cmdargs = ''
    for (key, value) in args:
        cmdargs += '&q=' + str(key) + ':' + str(value)
    cmd = 'curl -s -X GET --insecure "https://admin:admin@localhost:9200/%s/_search?size=1&pretty%s"' % (index, cmdargs)
    output = aggregator_ssh.ssh(cmd, output=True)
    return json.loads(output)


def test_application_get():

    # Test error in excalibur by not giving an appId.
    response = session.get(base_url + '/application/get')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    # Test error in endpoint by giving valid data with a predictable response that
    # only comes from the api endpoint.
    response = session.get(
        base_url + '/application/get', params={'appId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.user['invalidId']['result']

    result = __query_elasticsearch_excalibur(
        [('user', settings['user']), ('real_func_name', 'application_get'), ('app_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_role_get():

    response = session.get(base_url + '/role/get')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/role/get', params={'roleId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.user['invalidId']['result']

    result = __query_elasticsearch_excalibur(
        [('user', settings['user']), ('real_func_name', 'role_get'), ('role_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_user_role_list():

    # Kind of hard to make this fail.
    response = session.get(base_url + '/role/list')
    ls = response.json()
    assert type(ls) == list
    for obj in ls:
        assert set(obj.keys()) == set([
            'id', 'name', 'version', 'applicationIds', 'startingResourceIds',
            'startingTransducerIds', 'ipAddress'
        ])

    result = __query_elasticsearch_excalibur(
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
            'transducerIds', 'state', 'ipAddress'
        ])

    result = __query_elasticsearch_excalibur(
        [('user', settings['user']), ('real_func_name', 'user_virtue_list')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_virtue_get():

    response = session.get(base_url + '/virtue/get')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(
        base_url + '/virtue/get', params={'virtueId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.user['invalidId']['result']

    result = __query_elasticsearch_excalibur(
        [('user', settings['user']), ('real_func_name', 'virtue_get'), ('virtue_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0


def test_virtue_launch():

    response = session.get(base_url + '/virtue/launch')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    # Load aws_instance_info
    # Spin up a 'Virtue'
    aws = AWS()
    instance = aws.instance_create(
        image_id='ami-36a8754c',
        inst_type='t2.small',
        subnet_id=settings['subnet'],
        key_name='starlab-virtue-te',
        tag_key='Project',
        tag_value='Virtue',
        sec_group=settings['sec_group'],
        inst_profile_name='',
        inst_profile_arn=''
    )
    instance.stop()
    instance.wait_until_stopped()

    try:
        print(instance.private_ip_address)
        # Populate it in LDAP
        virtue = {
            'id': 'TEST_VIRTUE_LAUNCH',
            'username': 'jmitchell',
            'roleId': 'TBD',
            'applicationIds': [],
            'resourceIds': [],
            'transducerIds': [],
            'awsInstanceId': instance.id
        }
        ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
        inst.add_obj(ldap_virtue, 'virtues', 'cid', throw_error=True)

        # virtue_launch() it
        response = session.get(base_url + '/virtue/launch',
                               params={'virtueId': 'TEST_VIRTUE_LAUNCH'})
        assert response.text == json.dumps(ErrorCodes.user['success'])

        instance.reload()
        assert instance.state['Name'] == 'running'

        response = session.get(base_url + '/virtue/launch',
                               params={'virtueId': 'TEST_VIRTUE_LAUNCH'})
        assert response.text == json.dumps(ErrorCodes.user['virtueAlreadyLaunched']['result'])

        result = __query_elasticsearch_excalibur(
            [('user', settings['user']), ('real_func_name', 'virtue_launch'),
             ('virtue_id', 'TEST_VIRTUE_LAUNCH')])
        assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0

    except:
        raise
    finally:
        inst.del_obj('cid', 'TEST_VIRTUE_LAUNCH', objectClass='OpenLDAPvirtue')
        instance.terminate()


def test_virtue_stop():

    response = session.get(base_url + '/virtue/stop')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    # Load aws_instance_info
    # Spin up a 'Virtue'
    aws = AWS()
    instance = aws.instance_create(
        image_id='ami-36a8754c',
        inst_type='t2.small',
        subnet_id=settings['subnet'],
        key_name='starlab-virtue-te',
        tag_key='Project',
        tag_value='Virtue',
        sec_group=settings['sec_group'],
        inst_profile_name='',
        inst_profile_arn=''
    )

    try:
        # Populate it in LDAP
        virtue = {
            'id': 'TEST_VIRTUE_STOP',
            'username': 'jmitchell',
            'roleId': 'TBD',
            'applicationIds': [],
            'resourceIds': [],
            'transducerIds': [],
            'awsInstanceId': instance.id
        }
        ldap_virtue = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')
        inst.add_obj(ldap_virtue, 'virtues', 'cid', throw_error=True)

        # virtue_stop() it
        response = session.get(base_url + '/virtue/stop',
                               params={'virtueId': 'TEST_VIRTUE_STOP'})
        assert response.text == json.dumps(ErrorCodes.user['success'])

        instance.reload()
        assert instance.state['Name'] == 'stopped'

        response = session.get(base_url + '/virtue/stop',
                               params={'virtueId': 'TEST_VIRTUE_STOP'})
        assert response.text == json.dumps(ErrorCodes.user['virtueAlreadyStopped']['result'])

        result = __query_elasticsearch_excalibur(
            [('user', settings['user']), ('real_func_name', 'virtue_stop'),
             ('virtue_id', 'TEST_VIRTUE_STOP')])
        assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0

    except:
        raise
    finally:
        inst.del_obj('cid', 'TEST_VIRTUE_STOP', objectClass='OpenLDAPvirtue')
        instance.terminate()


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

    result = __query_elasticsearch_excalibur(
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

    result = __query_elasticsearch_excalibur(
        [('user', settings['user']), ('real_func_name', 'virtue_application_stop'),
         ('virtue_id', 'DoesNotExist'), ('app_id', 'DoesNotExist')])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0
