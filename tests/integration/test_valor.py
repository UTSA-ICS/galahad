import os
import sys

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(file_path))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)

import pytest

from website import valor


@pytest.fixture(scope='class')
def initialize_valor_api(request):

    valor_api = valor.ValorAPI()

    request.cls.valor_api = valor_api

    yield


@pytest.mark.usefixtures('initialize_valor_api')
class Test_ValorAPI:

    valor_id = None

    def test_valor_create(self):

        self.valor_id = self.valor_api.valor_create()


    @pytest.mark.skip
    def test_valor_destroy(self):

        self.valor_api.valor_destroy(self.valor_id)
