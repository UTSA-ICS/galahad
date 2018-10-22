import json
import os
import sys

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(file_path))) + '/excalibur'
sys.path.insert(0, base_excalibur_dir)
from cli.sso_login import sso_tool
from website.aws import AWS

def setup_module():

    global settings
    global ip

    with open('test_config.json', 'r') as infile:
        settings = json.load(infile)

    try:
        with open('../setup/excalibur_ip', 'r') as infile:
            ip = infile.read().strip()
    except:
        aws = AWS()
        ip = aws.get_public_ip()

    ip = ip + ':' + settings['port']

    with open('test_config.json', 'w') as outfile:
        json.dump(settings, outfile)


if (__name__ == '__main__'):

    setup_module()

    sso = sso_tool(ip)
    assert not sso.login(settings['user'], 'NotThePassword')
    assert sso.login(settings['user'], settings['password'])

    # Create the APP
    sso = sso_tool(ip)
    assert sso.login(settings['user'], settings['password'])

    assert sso.get_app_client_id('DoesNotExist') == None
    client_id = sso.get_app_client_id(settings['app_name'])

    if (client_id == None):
        client_id = sso.create_app(settings['app_name'],
                                   settings['redirect'].format(ip))
        assert client_id
    print client_id
