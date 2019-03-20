#!/usr/bin/python3

# Copyright (c) 2019 by Star Lab Corp.

import os
import sys
import time
import json
import requests

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(file_path))) + '/excalibur/cli'
sys.path.insert(0, base_excalibur_dir)
from sso_login import sso_tool

# Everything's installed and set up. Now we can just use the API for the final steps.

ip = 'excalibur.galahad.com:5002'
redirect = 'https://{0}/virtue/test'.format(ip)
app_name = 'TEST_APP'
verify_https = False

def login():

    global session

    sso = sso_tool(ip)
    assert sso.login('jmitchell@virtue.com', 'Test123!')

    client_id = sso.get_app_client_id(app_name)
    if (client_id == None):
        client_id = sso.create_app(app_name, redirect)
        assert client_id

    code = sso.get_oauth_code(client_id, redirect)
    assert code

    token = sso.get_oauth_token(client_id, code, redirect)
    assert 'access_token' in token

    session = requests.Session()
    session.headers = {
        'Authorization': 'Bearer {0}'.format(token['access_token'])
    }
    session.verify = verify_https

def user_call(path, **kwargs):

    url = 'https://{0}/virtue/user/{1}'.format(ip, path)
    args = {}

    for k in kwargs.keys():
        if (type(kwargs[k]) == dict or type(kwargs[k]) == list):
            args[k] = json.dumps(kwargs[k])
        else:
            args[k] = kwargs[k]

    response = session.get(url, params=args)
    assert response.status_code != 404

    return response.json()

def admin_call(relative_path, **kwargs):

    url = 'https://{0}/virtue/admin/{1}'.format(ip, relative_path)
    args = {}

    for k in kwargs.keys():
        if (type(kwargs[k]) == dict or type(kwargs[k]) == list):
            args[k] = json.dumps(kwargs[k])
        else:
            args[k] = kwargs[k]

    response = session.get(url, params=args)
    assert response.status_code != 404

    return response.json()

def security_call(relative_path, **kwargs):

    url = 'https://{0}/virtue/security/{1}'.format(ip, relative_path)
    args = {}

    for k in kwargs.keys():
        if (type(kwargs[k]) == dict or type(kwargs[k]) == list):
            args[k] = json.dumps(kwargs[k])
        else:
            args[k] = kwargs[k]

    response = session.get(url, params=args)
    assert response.status_code != 404

    return response.json()

if (__name__ == '__main__'):

    starting_roles = []

    starting_roles.append({
        'name': 'Document Editor',
        'version': '1.0',
        'applicationIds': [
            #'office-word',
            'firefox',
            # TODO: Add Excel app and uncomment office-word when we know it
            #       won't freeze the VM
        ],
        'startingResourceIds': [],
        'startingTransducerIds': [],
        'networkRules': []
    })

    starting_roles.append({
        'name': 'Windows Corporate Email User',
        'version': '1.0',
        'applicationIds': [
            #'office-outlook',
            'firefox',
            # TODO: Uncomment office-outlook when we know it won't freeze the VM
        ],
        'startingResourceIds': [],
        'startingTransducerIds': [],
        'networkRules': []
    })

    starting_roles.append({
        'name': 'Router Admin',
        'version': '1.0',
        'applicationIds': [
            'terminal',
            'firefox'
        ],
        'startingResourceIds': [],
        'startingTransducerIds': [],
        'networkRules': []
    })

    starting_roles.append({
        'name': 'Linux Corporate Email User',
        'version': '1.0',
        'applicationIds': [
            'thunderbird',
            'firefox'
        ],
        'startingResourceIds': [],
        'startingTransducerIds': [],
        'networkRules': []
    })

    starting_roles.append({
        'name': 'External Internet Consumer',
        'version': '1.0',
        'applicationIds': [
            'chrome',
            'skype'
        ],
        'startingResourceIds': [],
        'startingTransducerIds': [],
        'networkRules': []
    })

    starting_roles.append({
        'name': 'Linux and Windows Power User',
        'version': '1.0',
        'applicationIds': [
            'chrome',
            'terminal',
            'powershell',
            # TODO: Add Windows Command Terminal
        ],
        'startingResourceIds': [],
        'startingTransducerIds': [],
        'networkRules': []
    })

    login()

    for role in starting_roles:

        response = admin_call('role/create', role=role, unitySize='8GB')

        if (type(response) != dict):
            print(json.dumps(role, indent=4, sort_keys=True))
            print(response)
            exit(255)

        time.sleep(5)
