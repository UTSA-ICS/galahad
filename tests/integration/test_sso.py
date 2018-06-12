import json
import requests

from sso_login import sso_tool

def setup_module():

    global settings

    with open('test_config.json', 'r') as infile:
        settings = json.load(infile)

    with open('../setup/excalibur_ip', 'r') as infile:
        ip = infile.read().strip()

    ip = ip + ':' + settings['ip'].split(':')[1]
    settings['redirect'] = settings['redirect'].replace(settings['ip'], ip)
    settings['ip'] = ip

    with open('test_config.json', 'w') as outfile:
        json.dump(settings, outfile)

def test_login():

    sso = sso_tool(settings['ip'])
    assert not sso.login(settings['user'], 'NotThePassword')
    assert sso.login(settings['user'], settings['password'])

def test_create_app():

    sso = sso_tool(settings['ip'])
    assert sso.login(settings['user'], settings['password'])

    assert sso.get_app_client_id('DoesNotExist') == None
    client_id = sso.get_app_client_id(settings['app_name'])

    if(client_id == None):
        client_id = sso.create_app(settings['app_name'], settings['redirect'])
        assert client_id

def test_get_code():

    sso = sso_tool(settings['ip'])
    assert sso.login(settings['user'], settings['password'])

    client_id = sso.get_app_client_id(settings['app_name'])

    if(client_id == None):
        client_id = sso.create_app(settings['app_name'], settings['redirect'])
        assert client_id

    print('client_id: ' + client_id)

    assert sso.get_oauth_code('NotTheClientId', settings['redirect']) == None
    assert sso.get_oauth_code(client_id, 'NotARedirect') == None
    code = sso.get_oauth_code(client_id, settings['redirect'])
    assert code

def test_get_token():

    sso = sso_tool(settings['ip'])
    assert sso.login(settings['user'], settings['password'])

    client_id = sso.get_app_client_id(settings['app_name'])

    if(client_id == None):
        client_id = sso.create_app(settings['app_name'], settings['redirect'])
        assert client_id

    print('client_id: ' + client_id)

    code = sso.get_oauth_code(client_id, settings['redirect'])
    assert code
    print('code: ' + code)

    assert sso.get_oauth_token('NotTheClientId', code,
                               settings['redirect']) == None
    assert sso.get_oauth_token(client_id, 'NotTheCode',
                               settings['redirect']) == None
    assert sso.get_oauth_token(client_id, code, 'NotTheRedirect') == None
    token_data = sso.get_oauth_token(client_id, code, settings['redirect'])
    assert token_data
    assert 'access_token' in token_data
    print('access_token: ' + token_data['access_token'])

    token = token_data['access_token']
    res = requests.request('GET', ('https://{0}/virtue/user' +
                                    '/application/get').format(settings['ip']),
                           headers={'Authorization': 'Bearer {0}'.format(token)},
                           params={'appId': 'DoesNotExist'},
                           verify=settings['verify'])

    assert json.loads(res.text) == [10, 'The given ID is invalid.']

    with open('token_data.json', 'w') as outfile:
        json.dump(token_data, outfile)
