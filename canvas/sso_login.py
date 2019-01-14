import json
import requests
# To disable showing of insecure warnings for HTTPS without a certificate
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

verify_https = False


class sso_tool():
    def __init__(self, address):
        self.url = 'https://{0}'.format(address)
        self.session = requests.Session()
        self.token = None

    def get_csrf(self, html):

        csrf = None

        for s in html.split('\n'):
            s = s.strip()
            if (s[0:22] == '<input id="csrf_token"'):
                csrf = s.split('"')[-2]
                break

        return csrf

    def get_flask_traceback(self, html, print_output=True):

        if ('Traceback' not in html or 'DON\'T PANIC' not in html):
            # This is not a flask error traceback.
            return None

        split1 = html.split('-->')

        split2 = split1[-2].split('<!--')

        traceback = split2[-1].strip()

        if (print_output):
            print('Flask error:\n' + traceback)

        return traceback

    def login(self, email, password):

        login_prompt = self.session.get(
            self.url + '/account/login', verify=verify_https)

        csrf = self.get_csrf(login_prompt.text)

        if (csrf == None):
            traceback = self.get_flask_traceback(login_prompt.text)
            return None

        login_payload = {
            'csrf_token': csrf,
            'email': email,
            'password': password
        }

        login_response = self.session.post(
            self.url + '/account/login', login_payload, verify=verify_https)

        success = 'You are logged in' in login_response.text

        return success

    def get_app_client_id(self, name):

        response = self.session.get(self.url + '/client', verify=verify_https)
        lines = response.text.split('\n')

        for s in lines:
            s = s.strip()
            if (name in s):
                tmp = s.split('"')
                if (len(tmp) != 3):
                    return None
                return tmp[1].split('/')[3]

    def create_app(self, name, redirect_uri):

        app_prompt = self.session.get(
            self.url + '/client/2/create', verify=verify_https)

        csrf = self.get_csrf(app_prompt.text)

        if (csrf == None):
            self.get_flask_traceback(app_prompt.text)
            return None

        app_payload = {
            'csrf_token': csrf,
            'name': name,
            'allowed_grants': 'authorization_code',
            'allowed_scopes': 'email',
            'default_redirect_uri': '',
            'redirect_uris': redirect_uri,
            'website': self.url
        }

        app_response = self.session.post(
            self.url + '/client/2/create', app_payload, verify=verify_https)

        self.get_flask_traceback(app_response.text)

        return self.get_app_client_id(name)

    def get_oauth_code(self, client_id, redirect_uri):

        auth_payload = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri
        }

        auth_prompt = self.session.get(
            self.url + '/oauth2/authorize',
            params=auth_payload,
            verify=verify_https)

        csrf = self.get_csrf(auth_prompt.text)

        if (csrf == None):
            self.get_flask_traceback(auth_prompt.text)
            return None

        auth_payload['csrf_token'] = csrf

        auth_code_response = self.session.post(
            self.url + '/oauth2/authorize', auth_payload, verify=verify_https)

        if ('code:' not in auth_code_response.text):
            self.get_flask_traceback(auth_code_response.text)
            return None

        code = auth_code_response.text.split(':')[1]

        # For some reason, the code displayed on the page has an & at the end
        real_code = code[0:-1]
        return real_code

    def get_oauth_token(self, client_id, code, redirect_uri):

        token_payload = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'code': code,
            'redirect_uri': redirect_uri
        }

        token_response = self.session.post(
            self.url + '/oauth2/token', token_payload, verify=verify_https)

        if (token_response.status_code != 200):
            self.get_flask_traceback(token_response.text)
            return None

        return token_response.json()


if (__name__ == '__main__'):

    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Log in to Excalibur and save the user token')    
    parser.add_argument('-u', '--user', required=True, help='Username to log in with')
    parser.add_argument('-p', '--password', help='Password to use. If not specified, will prompt.')
    parser.add_argument('-o', '--outfile', default='usertoken.json', help='File to write access token to (default is usertoken.json)')
    parser.add_argument('-A', '--appid', default='APP_1', help='Application ID to use (default is APP_1)')
    parser.add_argument('server', help='Server address')

    args = parser.parse_args()

    if args.password is None:
        import getpass
        password = getpass.getpass('User password: ').strip()
        args.password = password

    print('Retrieving token')

    sso = sso_tool(args.server)
    if not sso.login(args.user, args.password):
        print('ERROR: Could not log in')
        sys.exit(1)

    redirect = 'https://{}/virtue/test'.format(args.server)

    client_id = sso.get_app_client_id(args.appid)
    if (client_id == None):
        client_id = sso.create_app(args.appid, redirect)
        assert client_id
    
    code = sso.get_oauth_code(client_id, redirect)
    if (code == None):
        print('Could not retrieve access code')
        sys.exit(1)

    token = sso.get_oauth_token(client_id, code, redirect)
    if (token == None):
        print('Could not retrieve token')
        sys.exit(1)

    with open(args.outfile, 'w') as outfile:
        json.dump(token, outfile, indent=4)
        outfile.write('\n')