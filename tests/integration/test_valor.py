#!/usr/bin/python

import os
import sys

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(file_path))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)
import time
import pytest
import rethinkdb

from website import valor
from website import apiendpoint
sys.path.insert(0, base_excalibur_dir + '/cli')
from website.services.errorcodes import ErrorCodes
from sso_login import sso_tool
from website.valor import RethinkDbManager
from website import ldap_tools
from website.ldaplookup import LDAP
import subprocess
import requests
import json
key_path = os.environ['HOME'] + '/galahad-keys/default-virtue-key.pem'
import time

def get_rethinkdb_connection():

    try:
        connection = rethinkdb.connect(
            host = 'rethinkdb.galahad.com',
            port = 28015,
            ssl = {
                'ca_certs':'/var/private/ssl/rethinkdb_cert.pem',
            }).repl()

    except Exception as error:
        print(error)

    return connection


def is_valor_in_rethinkdb(valor_id):

    connection = get_rethinkdb_connection()

    response = rethinkdb.db('transducers').table('galahad').filter({
        'host': valor_id
    }).run(connection)

    matching_valors = list(response)

    if matching_valors:
        return True

    return False


def is_valor_pingable(valor_id):

    connection = get_rethinkdb_connection()

    response = rethinkdb.db('transducers').table('galahad').filter({
        'host': valor_id
    }).run(connection)

    matching_valors = list(response)

    if matching_valors == []:
        return False

    ip_address = matching_valors[0]['address']

    response = os.system("ping -c 1 " + ip_address)

    if response == 0:
        return True

    return False


@pytest.fixture(scope='class')
def initialize_valor_api(request):

    valor_api = valor.ValorAPI()

    request.cls.valor_api = valor_api

    yield

'''
 This is a temp function due to poor maintainability
 TODO: NEED TO FIX
'''
def virtue_launch():

    global settings
    global inst
    global session
    global ip
    global base_url
    global test_valor_id

    with open('test_config.json', 'r') as infile:
        settings = json.load(infile)

    with open('../setup/aws_instance_info.json', 'r') as infile:
        tmp = json.load(infile)
        settings['subnet'] = tmp['subnet_id']
        settings['sec_group'] = tmp['sec_group']

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
    base_url = 'https://{0}/virtue/user'.format(ip)

    subprocess.call(['sudo', 'mkdir', '-p', '/mnt/efs/images/tests'])
    subprocess.check_call(['sudo', 'rsync', '/mnt/efs/images/unities/4GB.img',
                           '/mnt/efs/images/tests/4GB.img'])

    response = session.get('https://{0}/virtue/admin/valor/create'.format(ip))

    test_valor_id = response.json()['valor_id']

    response = session.get('https://{0}/virtue/admin/valor/launch'.format(ip),
                           params={'valor_id': test_valor_id})
    assert (response.json() == {'valor_id': test_valor_id})
  

    ############################################333
    response = session.get(base_url + '/virtue/launch')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    rethink_manager = RethinkDbManager()

    try:

        # 'Create' a Virtue
        subprocess.check_call(['sudo', 'mv', '/mnt/efs/images/tests/4GB.img',
                               ('/mnt/efs/images/provisioned_virtues/'
                                'TEST_VIRTUE_LAUNCH.img')])

        virtue = {
            'id': 'TEST_VIRTUE_LAUNCH',
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

        assert xl_list.count('\n') == 3

        response = session.get(base_url + '/virtue/launch',
                               params={'virtueId': 'TEST_VIRTUE_LAUNCH'})
        assert response.text == json.dumps(ErrorCodes.user['virtueAlreadyLaunched']['result'])

    except:
        raise
    finally:
        inst.del_obj('cid', 'TEST_VIRTUE_LAUNCH', objectClass='OpenLDAPvirtue')
        rethink_manager.remove_virtue('TEST_VIRTUE_LAUNCH')
        subprocess.check_call(['sudo', 'mv',
                               ('/mnt/efs/images/provisioned_virtues/'
                                'TEST_VIRTUE_LAUNCH.img'),
                               '/mnt/efs/images/tests/4GB.img'])

    return (real_virtue['id'], rethink_valor['address'])
'''
END of bad functions
'''



def is_virtue_running(key_path, ip_address):

        xl_list = subprocess.check_output(
            ['ssh', '-i', key_path, 'ubuntu@' + ip_address,
             '-o', 'StrictHostKeyChecking=no',
             'sudo xl list'])

        return xl_list.count('\n') == 3


def get_valor_ip(valor_id):

    connection = get_rethinkdb_connection()

    response = rethinkdb.db('transducers').table('galahad').filter(
        {'function': 'valor', 'host': valor_id}).run()

    valor = list(response.items)

    return valor['address']
    



@pytest.mark.usefixtures('initialize_valor_api')
class Test_ValorAPI:

    valor_id = None

    '''
    def test_valor_create(self):

        valor_id = self.valor_api.valor_create()

        Test_ValorAPI.valor_id = valor_id

        assert is_valor_in_rethinkdb(valor_id)
        assert not is_valor_pingable(valor_id)


    def test_valor_launch(self):

        valor_id = Test_ValorAPI.valor_id

        self.valor_api.valor_launch(valor_id)

        time.sleep(120)

        assert is_valor_in_rethinkdb(valor_id)
        assert is_valor_pingable(valor_id)


    def test_valor_stop(self):

        valor_id = Test_ValorAPI.valor_id

        self.valor_api.valor_stop(valor_id)

        assert is_valor_in_rethinkdb(valor_id)
        assert not is_valor_pingable(valor_id)


    def test_valor_destroy(self):

        valor_id = Test_ValorAPI.valor_id

        self.valor_api.valor_destroy(valor_id)

        assert not is_valor_in_rethinkdb(valor_id)
        assert not is_valor_pingable(valor_id)


    def test_valor_create_pool(self):

        number_of_valors = 0

        valor_ids = self.valor_api.valor_create_pool(number_of_valors)

        for valor_id in valor_ids:

            assert is_valor_in_rethinkdb(valor_id)
            assert is_valor_pingable(valor_id)

            self.valor_api.valor_destroy(valor_id)

    '''

    def test_valor_migrate_virtue(self):

        virtue_id, valor_ip_address = virtue_launch()

        destination_valor_id = self.valor_api.valor_create()

        destination_valor_ip_address = get_valor_ip(
            destination_valor_id)

        valor_api.valor_migrate_virtue(virtue_id, destination_valor_id)

        time.sleep(5) 
        assert not is_virtue_running(valor_ip_address) 
        assert is_virtue_running(destination_valor_ip_address)
