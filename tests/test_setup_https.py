import json
import requests

from sso_login import sso_tool

def test_get_token():

    with open('test_config.json') as infile:
        settings = json.load(infile)

    sso = sso_tool(settings['ip'])
    assert not sso.login(settings['user'], 'NotThePassword')
    assert sso.login(settings['user'], settings['password'])

    assert sso.get_app_client_id('DoesNotExist') == None
    client_id = sso.get_app_client_id(settings['app_name'])

    if(client_id == None):
        client_id = sso.create_app(settings['app_name'], settings['redirect'])
        assert client_id

    print('client_id: ' + client_id)

    assert sso.get_oauth_code('NotTheClientId', settings['redirect']) == None
    assert sso.get_oauth_code(client_id, 'NotARedirect') == None
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
                           verify=False)

    assert json.loads(res.text) == [10, 'The given ID is invalid.']

    with open('token_data.json', 'w') as outfile:
        json.dump(token_data, outfile)
