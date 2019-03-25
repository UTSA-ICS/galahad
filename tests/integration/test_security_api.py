# Copyright (c) 2019 by Star Lab Corp.

import datetime
import json
import os
import sys
import time

import integration_common

# For ssh_tool
sys.path.insert(0, '..')

from ssh_tool import ssh_tool

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(file_path))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)

from website.services.errorcodes import ErrorCodes

EXCALIBUR_HOSTNAME = 'excalibur.galahad.com'
AGGREGATOR_HOSTNAME = 'aggregator.galahad.com'

def setup_module():
    global virtue_ssh
    global virtue_id
    global aggregator_ssh

    global session
    global security_url

    session, admin_url, security_url, user_url = integration_common.create_session()

    virtue_id = None
    virtue_ssh = None

    aggregator_ssh = ssh_tool('ubuntu', AGGREGATOR_HOSTNAME, sshkey='~/default-user-key.pem')

    with open('../../excalibur/cli/excalibur_config.json', 'r') as f:
        config = json.load(f)
        session.get(security_url + '/api_config', params={'configuration': json.dumps(config)})

# This is a separate method that is NOT called from setup_module because pytest likes to run
# setup_module when, for example, listing tests instead of running them.
def __setup_virtue():
    global virtue_id
    global virtue_ssh
    global new_virtue
    global role_id

    virtue_ip = None
    # Read the Virtue IP and ID from a file (if they have been provided)
    if os.path.isfile('virtue_ip') and os.path.isfile('virtue_id'):
        new_virtue = False
        with open('virtue_ip', 'r') as infile:
            virtue_ip = infile.read().strip()
        with open('virtue_id', 'r') as infile:
            virtue_id = infile.read().strip()
    # Otherwise, create a new Virtue
    else:
        new_virtue = True
        role = integration_common.create_new_role('SecurityTestRole')
        virtue = integration_common.create_new_virtue('slapd', role['id'])
        virtue_ip = virtue['ipAddress']
        virtue_id = virtue['id']
        role_id = virtue['roleId']

    assert virtue_ip is not None

    virtue_ssh = ssh_tool('virtue', virtue_ip, sshkey='~/default-user-key.pem')

    # Check that the virtue is ready and reachable via ssh
    assert virtue_ssh.check_access()


def test_merlin_running():
    if virtue_ssh is None:
        __setup_virtue()

    # This needs to succeed in order for the rest of the tests to work, so wait in case it's still
    # in the process of starting up
    num_retries = 0
    max_retries = 5
    while num_retries < max_retries:
        ret = virtue_ssh.ssh('systemctl status merlin', test=False)
        if ret == 0:
            break
        time.sleep(30)
    assert num_retries < max_retries

def test_syslog_ng_running():
    if virtue_ssh is None:
        __setup_virtue()

    # This needs to succeed in order for the rest of the tests to work, so wait in case it's still
    # in the process of starting up
    num_retries = 0
    max_retries = 5
    while num_retries < max_retries:
        ret = virtue_ssh.ssh('systemctl status syslog-ng', test=False)
        if ret == 0:
            break
        time.sleep(30)
    assert num_retries < max_retries

def test_check_merlin_logs():
    if virtue_ssh is None:
        __setup_virtue()

    assert virtue_ssh.ssh('! ( tail -5 /opt/merlin/merlin.log | grep ERROR )') == 0

def test_list_transducers():
    if virtue_ssh is None:
        __setup_virtue()

    transducers = json.loads(session.get(security_url + '/transducer/list').text)
    assert len(transducers) > 1

def test_get():
    if virtue_ssh is None:
        __setup_virtue()

    result = session.get(security_url + '/transducer/get', params={
        'transducerId': 'path_mkdir'
    }).text
    transducer = json.loads(result)
    assert 'id' in transducer
    assert transducer['id'] == 'path_mkdir'

def __get_elasticsearch_index():
    # A new index is created every day
    now = datetime.datetime.now()
    index = now.strftime('syslog-%Y.%m.%d')
    return index

def __query_elasticsearch(args):
    assert aggregator_ssh.check_access()

    index = __get_elasticsearch_index()
    cmdargs = ''
    for (key, value) in args:
        cmdargs += '&q=' + str(key) + ':' + str(value)
    cmd = 'curl -s -X GET --insecure "https://admin:admin@localhost:9200/%s/_search?size=1&pretty%s"' % (index, cmdargs)
    output = aggregator_ssh.ssh(cmd, output=True)
    return json.loads(output)

def __get_merlin_index():
    # A new index is created every day
    now = datetime.datetime.now()
    index = now.strftime('merlin-%Y.%m.%d')
    return index

def __query_elasticsearch_merlin(args):
    index = __get_merlin_index()
    cmdargs = ''
    for (key, value) in args:
        cmdargs += '&q=' + str(key) + ':' + str(value)
    cmd = 'curl -s -X GET --insecure "https://admin:admin@localhost:9200/%s/_search?size=1&pretty%s"' % (index, cmdargs)
    output = aggregator_ssh.ssh(cmd, output=True)
    return json.loads(output)

def __get_excalibur_index():
    # A new index is created every day
    now = datetime.datetime.now()
    index = now.strftime('excalibur-%Y.%m.%d')
    return index

def __query_elasticsearch_excalibur(args):
    index = __get_excalibur_index()
    cmdargs = ''
    for (key, value) in args:
        cmdargs += '&q=' + str(key) + ':' + str(value)
    cmd = 'curl -s -X GET --insecure "https://admin:admin@localhost:9200/%s/_search?size=1&pretty%s"' % (index, cmdargs)
    output = aggregator_ssh.ssh(cmd, output=True)
    return json.loads(output)

def test_sensor_disable():
    if virtue_ssh is None:
        __setup_virtue()

    # Disable a sensor transducer
    response = session.get(security_url + '/transducer/disable', params={
        'transducerId': 'path_mkdir', 
        'virtueId': virtue_id
    })
    assert response.text == json.dumps(ErrorCodes.security['success'])

    # Just in case, give it a few seconds to receive and enfore the rule
    time.sleep(15)

    # Trigger sensor
    dirname = 'testdir_' + str(int(time.time()))
    virtue_ssh.ssh('mkdir ' + dirname)

    # Give elasticsearch a few seconds to receive the new logs
    time.sleep(60)

    # Check that the log DIDN'T appear on elasticsearch
    result = __query_elasticsearch([('LogType', 'Virtue'), ('Event', 'path_mkdir'), ('Child', dirname)])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] == 0

    result = __query_elasticsearch_merlin(
        [('transducer_id', 'path_mkdir'), ('enabled', 'false'), ('virtue_id', virtue_id)])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0

    result = __query_elasticsearch_excalibur([('transducer_id', 'path_mkdir'),
                                              ('real_func_name', 'transducer_disable'),
                                              ('virtue_id', virtue_id)])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0

    # Cleanup
    virtue_ssh.ssh('rm -r ' + dirname)

def test_sensor_enable():
    if virtue_ssh is None:
        __setup_virtue()

    # Enable a sensor transducer
    response = session.get(security_url + '/transducer/enable', params={
        'transducerId': 'path_mkdir', 
        'virtueId': virtue_id,
        'configuration': '{}'
    })
    assert response.text == json.dumps(ErrorCodes.security['success'])

    # Just in case, give it a few seconds to receive and enfore the rule
    time.sleep(15)

    # Trigger sensor
    dirname = 'testdir_' + str(int(time.time()))
    virtue_ssh.ssh('mkdir ' + dirname)

    # Give elasticsearch a few seconds to receive the new logs
    time.sleep(60)

    # Check that the log appeared on elasticsearch
    result = __query_elasticsearch([('LogType', 'Virtue'), ('Event', 'path_mkdir'), ('Child', dirname)])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0

    result = __query_elasticsearch_merlin(
        [('transducer_id', 'path_mkdir'), ('enabled', 'true'), ('virtue_id', virtue_id)])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0

    result = __query_elasticsearch_excalibur(
        [('transducer_id', 'path_mkdir'), ('real_func_name', 'transducer_enable'), ('virtue_id', virtue_id)])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0

    # Cleanup
    virtue_ssh.ssh('rm -r ' + dirname)

# Make sure the get_enabled and get_config tests come after sensor_enable and sensor_disable or else
# the results won't match.
def test_get_enabled():
    if virtue_ssh is None:
        __setup_virtue()

    result = session.get(security_url + '/transducer/get_enabled', params={
        'transducerId': 'path_mkdir',
        'virtueId': virtue_id
    }).text
    transducer = json.loads(result)
    assert type(transducer) is dict
    assert 'enabled' in transducer
    assert transducer['enabled'] == True

def test_get_config():
    if virtue_ssh is None:
        __setup_virtue()

    result = session.get(security_url + '/transducer/get_configuration', params={
        'transducerId': 'path_mkdir',
        'virtueId': virtue_id
    }).text
    config = json.loads(result)
    assert len(config) == 0

def test_list_enabled():
    if virtue_ssh is None:
        __setup_virtue()

    result = session.get(security_url + '/transducer/list_enabled', params={
        'virtueId': virtue_id
    }).text
    transducers = json.loads(result)
    assert type(transducers) is list
    assert len(transducers) >= 1
    assert type(transducers[0]) is not int

def test_actuator_kill_proc():
    # Start a long-running process
    virtue_ssh.ssh('nohup yes &> /dev/null &')

    # Check that it's running
    virtue_ssh.ssh('ps aux | grep yes | grep -v grep')

    # Kill the process via an actuator
    response = session.get(security_url + '/transducer/enable', params={
        'transducerId': 'kill_proc',
        'virtueId': virtue_id,
        'configuration': '{"processes":["yes"]}'
    })
    assert response.text == json.dumps(ErrorCodes.security['success'])

    # Just in case, give it a few seconds to propagate the rule
    time.sleep(15)

    # Check that the process is no longer running
    virtue_ssh.ssh('! ( ps aux | grep yes | grep -v grep)')

    # Disable the actuator
    response = session.get(security_url + '/transducer/disable', params={
        'transducerId': 'kill_proc',
        'virtueId': virtue_id
    })
    assert response.text == json.dumps(ErrorCodes.security['success'])

def test_actuator_net_block():
    # Try contacting a server - let's pick 1.1.1.1 (the public DNS resolver) because its IP is easy
    assert virtue_ssh.ssh('wget 1.1.1.1 -T 20 -t 1') == 0

    # Block the server
    response = session.get(security_url + '/transducer/enable', params={
        'transducerId': 'block_net',
        'virtueId': virtue_id,
        'configuration': '{"rules":["block_outgoing_dst_ipv4_1.1.1.1"]}'
    })
    assert response.text == json.dumps(ErrorCodes.security['success'])

    # Just in case, give it a few seconds to propagate the rule
    time.sleep(15)

    # Try contacting the server again - should fail now
    assert virtue_ssh.ssh('! (wget 1.1.1.1 -T 20 -t 1)') == 0

    # Unblock the server
    response = session.get(security_url + '/transducer/disable', params={
        'transducerId': 'block_net',
        'virtueId': virtue_id
    })
    assert response.text == json.dumps(ErrorCodes.security['success'])


def teardown_module():
    if virtue_id is not None:
        # Only delete a Virtue if it was created during these tests, not passed in manually
        if new_virtue:
            # Cleanup the new virtue created
            integration_common.cleanup_virtue('slapd', virtue_id)
            # Cleanup the new role created
            integration_common.cleanup_role('slapd', role_id)
