#!/usr/bin/python

import os
import subprocess
import sys
import time
import json

import pytest
import rethinkdb

import integration_common

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(file_path))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)

from website import valor
from website.valor import RethinkDbManager


key_path = os.environ['HOME'] + '/galahad-keys/default-virtue-key.pem'


def setup_module():

    global virtue
    global role
    global session
    global admin_url

    virtue = None
    role = None

    session, admin_url, security_url, user_url = \
        integration_common.create_session()


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
        'valor_id': valor_id
    }).run(connection)

    matching_valors = list(response)

    if matching_valors:
        return True

    return False


def is_valor_pingable(valor_id):

    connection = get_rethinkdb_connection()

    response = rethinkdb.db('transducers').table('galahad').filter({
        'valor_id': valor_id
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


def virtue_launch():

    global virtue
    global role

    # Create a new role
    role = integration_common.create_new_role('ValorTestMigrateVirtueRole')

    virtue = integration_common.create_new_virtue('slapd', role['id'])

    try:
        rethinkdb_manager = RethinkDbManager()

        rethinkdb_virtue = rethinkdb_manager.get_virtue(virtue['id'])

        assert type(rethinkdb_virtue) == dict

        rethinkdb_valors = rethinkdb_manager.list_valors()
        rethinkdb_valor = None
        for valor in rethinkdb_valors:
            if (valor['address'] == rethinkdb_virtue['address']):
                rethinkdb_valor = valor
                break

        assert rethinkdb_valor != None

        sysctl_stat = subprocess.call(
            ['ssh', '-i', key_path, 'ubuntu@' + rethinkdb_virtue['address'],
             '-o', 'StrictHostKeyChecking=no',
             'sudo systemctl status gaius'])

        # errno=3 means that gaius isn't running
        assert sysctl_stat == 0

        xl_list = subprocess.check_output(
            ['ssh', '-i', key_path, 'ubuntu@' + rethinkdb_virtue['address'],
             '-o', 'StrictHostKeyChecking=no',
             'sudo xl list'])

        assert xl_list.count('\n') == 3
    except:
        # Cleanup the new virtue created
        integration_common.cleanup_virtue('slapd', virtue['id'])

        # Cleanup the new role created
        integration_common.cleanup_role('slapd', role['id'])

        raise

    return (rethinkdb_virtue['virtue_id'], rethinkdb_valor['address'])


def is_virtue_running(ip_address):

        xl_list = subprocess.check_output(
            ['ssh', '-i', key_path, 'ubuntu@' + ip_address,
             '-o', 'StrictHostKeyChecking=no',
             'sudo xl list'])

        return xl_list.count('\n') == 3


def get_valor_ip(valor_id):

    connection = get_rethinkdb_connection()

    response = rethinkdb.db('transducers').table('galahad').filter(
        {'function': 'valor', 'valor_id': valor_id}).run()

    valor = list(response.items)[0]

    return valor['address']
    

@pytest.mark.usefixtures('initialize_valor_api')
class Test_ValorAPI:

    valor_id = None


    def test_valor_create(self):

        valor_id = self.valor_api.valor_create()

        Test_ValorAPI.valor_id = valor_id

        assert is_valor_in_rethinkdb(valor_id)
        assert not is_valor_pingable(valor_id)


    def test_valor_launch(self):

        valor_id = Test_ValorAPI.valor_id

        self.valor_api.valor_launch(valor_id)

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


    def test_valor_migrate_virtue(self):

        global virtue
        global role

        virtue_id, valor_ip_address = virtue_launch()

        print("\nSource Valor IP Is {}\n".format(valor_ip_address))

        destination_valor_id = json.loads(
            session.get(admin_url + '/valor/migrate_virtue',
                        params={'virtue_id': virtue_id}).text)

        destination_valor_ip_address = get_valor_ip(
            destination_valor_id['valor_id'])

        print("\nTarget valor IP is {}\n".format(destination_valor_ip_address))

        time.sleep(60)

        assert not is_virtue_running(valor_ip_address) 
        assert is_virtue_running(destination_valor_ip_address)

        # Cleanup the new virtue created
        integration_common.cleanup_virtue('slapd', virtue['id'])
        virtue = None

        # Cleanup the new role created
        integration_common.cleanup_role('slapd', role['id'])
        role = None

        # Cleanup the used valor node
        json.loads(session.get(admin_url + '/valor/destroy', params={
            'valor_id': destination_valor_id['valor_id']}).text)


def teardown_module():

    if virtue:

        # Cleanup the new virtue created
        integration_common.cleanup_virtue('slapd', virtue['id'])

        # Cleanup the new role created
        integration_common.cleanup_role('slapd', role['id'])
