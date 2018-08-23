import pytest
import json
import os
import sys
import time
import datetime
import boto3
import requests

from integration_common import create_new_virtue

# For excalibur methods (API, etc)
file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(file_path)) + '/../excalibur'
sys.path.insert(0, base_excalibur_dir)

# For common.py
sys.path.insert(0, '..')

from common import ssh_tool
from website import ldap_tools
from website.ldaplookup import LDAP
from website.apiendpoint import EndPoint
from website.apiendpoint_admin import EndPoint_Admin
from website.apiendpoint_security import EndPoint_Security
from website.services.errorcodes import ErrorCodes
from website.aws import AWS
from website.controller import CreateVirtueThread

sys.path.insert(0, base_excalibur_dir + '/cli')
from sso_login import sso_tool

def setup_module():
    global virtue_ssh
    global aggregator_ssh
    global virtue_id
    global virtue_ip

    global session
    global base_url
    global inst

    settings = None
    with open('test_config.json', 'r') as infile:
        settings = json.load(infile)

    excalibur_ip = None
    with open('../setup/excalibur_ip', 'r') as infile:
        excalibur_ip = infile.read().strip() + ':' + settings['port']

    aggregator_ip = None
    with open('../setup/aggregator_ip', 'r') as infile:
        aggregator_ip = infile.read().strip()

    inst = LDAP('', '')
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s(dn, 'Test123!')


    # Connect to Excalibur's REST interface
    redirect = settings['redirect'].format(excalibur_ip)

    sso = sso_tool(excalibur_ip)
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

    base_url = 'https://{0}/virtue/security'.format(excalibur_ip)


    virtue_ip = None
    virtue_id = None
    virtue_ssh = None

    aggregator_ssh = ssh_tool('ubuntu', aggregator_ip, sshkey='~/default-user-key.pem')

    with open('../../excalibur/cli/excalibur_config.json', 'r') as f:
        config = json.load(f)
        session.get(base_url + '/api_config', params={'configuration': json.dumps(config)})

# This is a separate method that is NOT called from setup_module because pytest likes to run
# setup_module when, for example, listing tests instead of running them.
def __setup_virtue():
    global virtue_ip
    global virtue_id
    global virtue_ssh

    # Read the Virtue IP and ID from a file (if they have been provided)
    if os.path.isfile('../setup/virtue_ip') and os.path.isfile('../setup/virtue_id'):
        with open('../setup/virtue_ip', 'r') as infile:
            virtue_ip = infile.read().strip()
        with open('../setup/virtue_id', 'r') as infile:
            virtue_id = infile.read().strip()
    # Otherwise, create a new Virtue
    else:
        role = {
            'name': 'SecurityTestRole',
            'version': '1.0',
            'applicationIds': [],
            'startingResourceIds': [],
            'startingTransducerIds': []
        }

        virtue = create_new_virtue(inst, role, 'jmitchell')
        virtue_ip = virtue['ipAddress']
        virtue_id = virtue['id']

    assert virtue_ip is not None

    virtue_ssh = ssh_tool('ubuntu', virtue_ip, sshkey='~/default-user-key.pem')

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

    transducers = json.loads(session.get(base_url + '/transducer/list').text)
    assert len(transducers) > 1

def __get_elasticsearch_index():
    # A new index is created every day
    now = datetime.datetime.now()
    index = now.strftime('syslog-%Y.%m.%d')
    return index

def __query_elasticsearch(args):
    index = __get_elasticsearch_index()
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
    session.get(base_url + '/transducer/disable', params={
        'transducerId': 'path_mkdir', 
        'virtueId': virtue_id
    })

    # Just in case, give it a few seconds to receive and enfore the rule
    time.sleep(15)

    # Trigger sensor
    dirname = 'testdir_' + str(int(time.time()))
    virtue_ssh.ssh('mkdir ' + dirname)

    # Give elasticsearch a few seconds to receive the new logs
    time.sleep(15)

    # Check that the log DIDN'T appear on elasticsearch
    result = __query_elasticsearch([('LogType', 'Virtue'), ('Event', 'path_mkdir'), ('Child', dirname)])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] == 0

    # Cleanup
    virtue_ssh.ssh('rm -r ' + dirname)

def test_sensor_enable():
    if virtue_ssh is None:
        __setup_virtue()

    # Enable a sensor transducer
    session.get(base_url + '/transducer/enable', params={
        'transducerId': 'path_mkdir', 
        'virtueId': virtue_id,
        'configuration': '{}'
    })

    # Just in case, give it a few seconds to receive and enfore the rule
    time.sleep(15)

    # Trigger sensor
    dirname = 'testdir_' + str(int(time.time()))
    virtue_ssh.ssh('mkdir ' + dirname)

    # Give elasticsearch a few seconds to receive the new logs
    time.sleep(15)

    # Check that the log appeared on elasticsearch
    result = __query_elasticsearch([('LogType', 'Virtue'), ('Event', 'path_mkdir'), ('Child', dirname)])
    assert 'hits' in result and 'total' in result['hits'] and result['hits']['total'] > 0

    # Cleanup
    virtue_ssh.ssh('rm -r ' + dirname)

