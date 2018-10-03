file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(file_path))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)

import pytest

from website import valor


@pytest.fixture(scope='class')
def initialize_valor_api():

    valor_api = valor.ValorAPI()

    yield valor_api


@pytest.mark.usefixtures('initialize_valor_api')
class Test_ValorAPI:


    def test_valor_create(self):

        valor.valor_create()
