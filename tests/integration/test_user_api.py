import os
import sys
import json
import requests

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(os.path.dirname(os.path.dirname(file_path))) + '/flask-authlib'
sys.path.insert(0, base_excalibur_dir)
from website.services.errorcodes import ErrorCodes

##
# Functionality of these API commands is tested by unit/test_user_api.py.
# These tests verify that the return values get into the https response correctly.
##

def setup_module():

    global settings
    global token_data
    global session
    global base_url

    with open('test_config.json', 'r') as infile:
        settings = json.load(infile)

    with open('token_data.json', 'r') as infile:
        token_data = json.load(infile)

    session = requests.Session()
    session.headers = {'Authorization':
                       'Bearer {0}'.format(token_data['access_token'])}
    session.verify = settings['verify']

    base_url = 'https://{0}/virtue/user'.format(settings['ip'])

def test_application_get():

    # Test error in excalibur by not giving an appId.
    res = session.get(base_url + '/application/get')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    # Test error in endpoint by giving valid data with a predictable response that
    # only comes from the api endpoint.
    res = session.get(base_url + '/application/get',
                      params={'appId': 'DoesNotExist'})
    assert res.json() == ErrorCodes.user['invalidId']['result']

def test_role_get():

    res = session.get(base_url + '/role/get')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/role/get',
                      params={'roleId': 'DoesNotExist'})
    assert res.json() == ErrorCodes.user['invalidId']['result']

def test_user_role_list():

    # Kind of hard to make this fail.
    res = session.get(base_url + '/role/list')
    obj = res.json()
    assert type(obj) == list
    if(len(obj) > 0):
        assert 'id' in obj[0]
        assert 'name' in obj[0]

def test_user_virtue_list():

    # Kind of hard to make this fail.
    res = session.get(base_url + '/virtue/list')
    obj = res.json()
    assert type(obj) == list
    if(len(obj) > 0):
        assert 'id' in obj[0]
        assert 'username' in obj[0]

def test_virtue_get():

    res = session.get(base_url + '/virtue/get')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/virtue/get',
                      params={'virtueId': 'DoesNotExist'})
    assert res.json() == ErrorCodes.user['invalidId']['result']

def test_virtue_create():

    res = session.get(base_url + '/virtue/create')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/virtue/create',
                      params={'roleId': 'DoesNotExist'})
    assert res.json() == ErrorCodes.user['invalidRoleId']['result']

def test_virtue_launch():

    res = session.get(base_url + '/virtue/launch')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/virtue/launch',
                      params={'virtueId': 'DoesNotExist'})
    assert res.json() == ErrorCodes.user['invalidId']['result']

def test_virtue_stop():
    
    res = session.get(base_url + '/virtue/stop')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/virtue/stop',
                      params={'virtueId': 'DoesNotExist'})
    assert res.json() == ErrorCodes.user['invalidId']['result']

def test_virtue_destroy():

    res = session.get(base_url + '/virtue/destroy')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/virtue/destroy',
                      params={'virtueId': 'DoesNotExist'})
    assert res.json() == ErrorCodes.user['invalidId']['result']

def test_virtue_application_launch():

    res = session.get(base_url + '/application/launch')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/application/launch',
                      params={'virtueId': 'DoesNotExist',
                              'appId': 'DoesNotExist'})
    assert (res.json() == ErrorCodes.user['invalidVirtueId']['result']
            or res.json() == ErrorCodes.user['invalidApplicationId']['result'])

def test_virtue_application_stop():

    res = session.get(base_url + '/application/stop')
    assert res.json() == ErrorCodes.user['unspecifiedError']['result']

    res = session.get(base_url + '/application/stop',
                      params={'virtueId': 'DoesNotExist',
                              'appId': 'DoesNotExist'})
    assert (res.json() == ErrorCodes.user['invalidVirtueId']['result']
            or res.json() == ErrorCodes.user['invalidApplicationId']['result'])

