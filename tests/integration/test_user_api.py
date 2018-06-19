import os
import sys
import json
import requests

from sso_login import sso_tool

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(os.path.dirname(os.path.dirname(file_path))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)
from website.services.errorcodes import ErrorCodes

##
# Functionality of these API commands is tested by unit/test_user_api.py.
# These tests verify that the return values get into the https response correctly.
##

def setup_module():

    global settings
    global session
    global base_url

    with open('test_config.json', 'r') as infile:
        settings = json.load(infile)

    with open('../setup/excalibur_ip', 'r') as infile:
        ip = infile.read().strip() + ':' + settings['port']

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
    session.headers = {'Authorization':
                       'Bearer {0}'.format(token['access_token'])}
    session.verify = settings['verify']

    base_url = 'https://{0}/virtue/user'.format(ip)

def test_application_get():

    # Test error in excalibur by not giving an appId.
    response = session.get(base_url + '/application/get')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    # Test error in endpoint by giving valid data with a predictable response that
    # only comes from the api endpoint.
    response = session.get(base_url + '/application/get',
                      params={'appId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.user['invalidId']['result']

def test_role_get():

    response = session.get(base_url + '/role/get')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(base_url + '/role/get',
                      params={'roleId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.user['invalidId']['result']

def test_user_role_list():

    # Kind of hard to make this fail.
    response = session.get(base_url + '/role/list')
    ls = response.json()
    assert type(ls) == list
    for obj in ls:
        assert set(obj.keys()) == set(['id', 'name', 'version', 'applicationIds',
                                 'startingResourceIds', 'startingTransducerIds'])

def test_user_virtue_list():

    # Kind of hard to make this fail.
    response = session.get(base_url + '/virtue/list')
    ls = response.json()
    assert type(ls) == list
    for obj in ls:
        assert set(obj.keys()) == set(['id', 'username', 'roleId',
                                       'applicationIds', 'resourceIds',
                                       'transducerIds', 'state', 'ipAddress'])

def test_virtue_get():

    response = session.get(base_url + '/virtue/get')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(base_url + '/virtue/get',
                      params={'virtueId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.user['invalidId']['result']

def test_virtue_create():

    response = session.get(base_url + '/virtue/create')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(base_url + '/virtue/create',
                      params={'roleId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.user['invalidRoleId']['result']

def test_virtue_launch():

    response = session.get(base_url + '/virtue/launch')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(base_url + '/virtue/launch',
                      params={'virtueId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.user['invalidId']['result']

def test_virtue_stop():
    
    response = session.get(base_url + '/virtue/stop')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(base_url + '/virtue/stop',
                      params={'virtueId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.user['invalidId']['result']

def test_virtue_destroy():

    response = session.get(base_url + '/virtue/destroy')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(base_url + '/virtue/destroy',
                      params={'virtueId': 'DoesNotExist'})
    assert response.json() == ErrorCodes.user['invalidId']['result']

def test_virtue_application_launch():

    response = session.get(base_url + '/application/launch')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(base_url + '/application/launch',
                      params={'virtueId': 'DoesNotExist',
                              'appId': 'DoesNotExist'})
    assert (response.json() == ErrorCodes.user['invalidVirtueId']['result']
            or response.json() == ErrorCodes.user['invalidApplicationId']['result'])

def test_virtue_application_stop():

    response = session.get(base_url + '/application/stop')
    assert response.json() == ErrorCodes.user['unspecifiedError']['result']

    response = session.get(base_url + '/application/stop',
                      params={'virtueId': 'DoesNotExist',
                              'appId': 'DoesNotExist'})
    assert (response.json() == ErrorCodes.user['invalidVirtueId']['result']
            or response.json() == ErrorCodes.user['invalidApplicationId']['result'])

