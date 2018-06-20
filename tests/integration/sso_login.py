import json
import requests

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

    def login(self, email, password):

        login_prompt = self.session.get(
            self.url + '/account/login', verify=verify_https)

        csrf = self.get_csrf(login_prompt.text)

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
            return None

        auth_payload['csrf_token'] = csrf

        auth_code_response = self.session.post(
            self.url + '/oauth2/authorize', auth_payload, verify=verify_https)

        if ('code:' not in auth_code_response.text):
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
            return None

        return token_response.json()


if (__name__ == '__main__'):

    print('Retrieving token')

    sso = sso_tool('35.172.121.143:5002')
    sso.login('jmitchell@virtue.com', 'Test123!')

    redirect = 'https://35.172.121.143:5002/virtue/test'

    client_id = sso.get_app_client_id('TEST_APP')
    code = sso.get_oauth_code(client_id, redirect)
    token = sso.get_oauth_token(client_id, code, redirect)

    with open('token_data.json', 'w') as outfile:
        json.dump(token, outfile)
