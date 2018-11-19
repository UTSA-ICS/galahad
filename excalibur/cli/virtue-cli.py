#!/usr/bin/env python3

from endpoint import Endpoint

import json
import os
import os.path
import sys


if __name__ == '__main__':
    if 'VIRTUE_ADDRESS' not in os.environ:
        print('Please set VIRTUE_ADDRESS as an environment variable before using this script')
        sys.exit(1)
    ip = os.environ['VIRTUE_ADDRESS']

    # Get the user token from the token file - assume it's in usertoken.json, or specified in the env
    token = None
    if 'VIRTUE_TOKEN' in os.environ:
        token = json.loads(os.environ['VIRTUE_TOKEN'])
    else:
        if not os.path.isfile('usertoken.json'):
            token = None
        else:
            with open('usertoken.json', 'r') as tokenfile:
                token = json.load(tokenfile)
    if token is None:
        print('You must log in before using this command. Use sso_login.py to get a user token and save it in usertoken.json')
        sys.exit(1)

    # Instantiate the appropriate endpoint:
    #   virtue          --> user_api
    #   virtue-admin    --> admin_api
    #   virtue-security --> security_api
    procname = os.path.basename(sys.argv[0])
    ep = None
    if procname == 'virtue':
        ep = Endpoint.factory(Endpoint.EpType.USER, ip)
    elif procname == 'virtue-admin':
        ep = Endpoint.factory(Endpoint.EpType.ADMIN, ip)
    elif procname == 'virtue-security':
        ep = Endpoint.factory(Endpoint.EpType.SECURITY, ip)
    elif procname == 'virtue-cli.py':
        print('Please run this script through a symlink to virtue, virtue-admin, or virtue-security')
        sys.exit(1)
    else:
        print('Unknown endpoint')
        sys.exit(1)

    # Use the provided token to authenticate to the API endpoint
    ep.set_token(token)
    command_toks = []
    params = {}
    for tok in sys.argv[1:]:
        if tok.startswith('--'):
            subtok = tok.split('=')
            params[subtok[0].lstrip('--')] = subtok[1]
        else:
            command_toks.append(tok)
    
    command = ' '.join(command_toks)
    res = ep.handle_command(command, params)
    if res is not None:
        print(res)

# Parse out the parameters and check to make sure you have them all

# Call the correct method on the endpoint