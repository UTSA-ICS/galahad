# Copyright (c) 2019 by Star Lab Corp.

import argparse
import json
import sys
import requests
from collections import OrderedDict

from sso_login import sso_tool

if (__name__ == '__main__'):

    parser = argparse.ArgumentParser(
        description='Get the APP client ID and update the config.json file')
    parser.add_argument('-u', '--user', required=True, help='Username to log in with')
    parser.add_argument('-p', '--password',
                        help='Password to use. If not specified, will prompt.')
    parser.add_argument('-A', '--appid', default='APP_1', help='Application ID to use ('
                                                               'default is APP_1)')
    parser.add_argument('-s', '--server', default='excalibur.galahad.com:5002',
                        help='Server address')

    args = parser.parse_args()

    if args.password is None:
        import getpass

        password = getpass.getpass('User password: ').strip()
        args.password = password

    sso = sso_tool(args.server)
    if not sso.login(args.user, args.password):
        print('ERROR: Could not log in')
        sys.exit(1)

    redirect = 'https://{}/virtue/test'.format(args.server)
    redirect_canvas = 'https://{}/virtue/test\n' \
                      'http://canvas.com:3000/connect/excalibur/callback'.format(args.server)

    client_id = sso.get_app_client_id(args.appid)
    if (client_id == None):
        client_id = sso.create_app(args.appid, redirect_canvas)
        assert client_id

    print('The Client ID is {}'.format(client_id))

    with open('config.json', 'r') as filecontents:
        config = json.load(filecontents, object_pairs_hook=OrderedDict)

    config['excalibur']['key'] = client_id

    with open('config.json', 'w') as outfile:
        json.dump(config, outfile, indent=4)
        outfile.write('\n')

    code = sso.get_oauth_code(client_id, redirect)

    token_data = sso.get_oauth_token(client_id, code, redirect)

    key = requests.get(sso.url + '/virtue/user/key/get',
                       headers={
                           'Authorization': 'Bearer {0}'.format(token_data['access_token'])
                       },
                       verify=False).json()

    with open('key.pem', 'w') as key_file:
        key_file.write(key)
