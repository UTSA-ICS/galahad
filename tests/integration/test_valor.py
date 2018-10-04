import os
import sys

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(file_path))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)

import pytest
import rethinkdb

from website import valor


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


@pytest.mark.usefixtures('initialize_valor_api')
class Test_ValorAPI:

    valor_id = None


    def test_valor_create(self):

        valor_id = self.valor_api.valor_create()

        Test_ValorAPI.valor_id = valor_id

        assert is_valor_in_rethinkdb(valor_id)
        assert is_valor_pingable(valor_id)


    def test_valor_destroy(self):

        self.valor_api.valor_destroy(Test_ValorAPI.valor_id)
        assert not is_valor_in_rethinkdb(Test_ValorAPI.valor_id)
