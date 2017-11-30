import requests


class OneLogin(object):
    def __init__(self, shard='US'):
        """
        Specify the shard of the system being used (us or eu)
        :param shard: us or eu
        :return:
        """
        self.shard = shard.lower()
        if 'us' in self.shard:
            self.base_url = 'https://api.us.onelogin.com'
        elif 'eu' in self.shard:
            self.base_url = 'https://api.eu.onelogin.com'
        elif 'shadow01' in self.shard:
            self.base_url = 'https://oapi01-shadow01.use1.onlgn.net'

    def set_attributes(self, kwargs):
        for kwarg_key, kwarg_value in kwargs.iteritems():
            setattr(self, kwarg_key, kwarg_value)

    def handle_error(self, **kwargs):
        error = {}
        for k,v in kwargs.iteritems():
            error[k] = v
        return error


class Token(OneLogin):
    """
    Create the token object to be used for calling the OneLogin API.
    """
    def __init__(token, **kwargs):
        for key in ('client_id', 'client_secret', 'shard'):
            if key in kwargs:
                setattr(token, key, kwargs[key])
        token.session = requests.session()
        token.session.headers = {'Content-Type': 'application/json'}
        oauth_endpoint = '/auth/oauth2'
        try:
            OneLogin.__init__(token, token.shard)
        except:
            if token.client_id == '0':
                raise ValueError('Client_ID is required')
            elif token.client_secret == '0':
                raise ValueError('Client_Secret is required')
        token.target = token.base_url + oauth_endpoint
        token.get_token()

    def get_token(token):
        """
        Get a new OAUTH token
        :return:
        """
        authorization = 'client_id: %s, client_secret: %s' % (token.client_id,
                                                              token.client_secret)
        token.session.headers.update({'Authorization':authorization})
        r = token.session.post(token.target + '/token', verify=False,
                               json={'grant_type':'client_credentials'})
        if r.status_code != 200:
            print token.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': token.target + '/token',
                                       'headers':token.session.headers})
            return False
        else:
            token.set_attributes({
                'access_token':r.json()['data'][0]['access_token'],
                'refresh_token':r.json()['data'][0]['refresh_token'],
                'token_created_at':r.json()['data'][0]['created_at'],
                'token_expires_at':r.json()['data'][0]['expires_in']})
            return True

    def refresh_the_token(token):
        """
        Refresh the current OAUTH token
        :return:
        """
        r = token.session.post(token.target + '/token', verify=False,
                               json={
                                  'grant_type':'refresh_token',
                                  'refresh_token':token.refresh_token,
                                  'access_token':token.access_token})
        if r.status_code != 200:
            print token.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': token.target + '/token',
                                       'headers':token.session.headers})
            return False
        else:
            token.set_attributes({
                'access_token':r.json()['data'][0]['access_token'],
                'refresh_token':r.json()['data'][0]['refresh_token'],
                'created_at':r.json()['data'][0]['created_at'],
                'expires_in':r.json()['data'][0]['expires_in']
            })

            return True

    def revoke_the_token(token):
        """
        Revoke the current OAUTH token
        :return:
        """
        r = token.session.post(token.target + '/revoke', verify=False,
                               json={
                                  'grant_type':'revoke_token',
                                  'access_token':token.access_token,
                                  'client_id':token.client_id,
                                  'client_secret':token.client_secret
                              })
        if r.status_code != 200:
            print token.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': token.target + '/revoke',
                                       'headers':token.session.headers})
            return False
        else:
            return True

    def check_token_expiration(self):
        """
        TODO: Calculate expiration time of token, if expired, call refresh_token
        to update access_token
        :return:
        """

    def check_rate_limit(token):
        """
        check rate limit
        :return:
        """
        if token.access_token:
            authorization = 'Bearer:%s' % token.access_token
            token.session.headers.update({'Authorization':authorization})
        else:
            return 'Access Token not found'
        r = token.session.get(token.base_url + '/auth/rate_limit', verify=False)
        if r.status_code != 200:
            print token.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': token.target + '/revoke',
                                       'headers':token.session.headers})
            return False
        else:
            return r


class User(Token):
    """
    """

    def __init__(user, token):
        """
        :param kwargs:
        :return:
        """
        # user.set_attributes(kwargs)
        user.session = requests.session()
        user.session.headers = {'Content-Type': 'application/json'}
        user.user_endpoint = '/api/1/users'
        try:
            user.base_url = token.base_url
            user.session.headers.update({'Authorization': 'Bearer:%s' % token.access_token})
        except:
            raise ValueError('Token not found, have you initialized the Token yet?')
        # try:
        #     Token.__init__(user, **{'client_id':user.client_id,
        #                             'client_secret':user.client_secret,
        #                             'shard':user.shard})
        # except:
        #     if user.client_id == '0':
        #         raise ValueError('client_id is required')
        #     elif user.client_secret == '0':
        #         raise ValueError('client_secret is required')
        # try:
        #     user.session.headers.update({'Authorization': 'Bearer:%s' % user.access_token})
        # except:
        #     raise ValueError('invalid access_token, please check your client_id'
        #                      ' and client_secret, did you specify the shard')

    def get_all_users(user, sort=False, fields=''):
        """
        Get all users, specify sort and fields to filter results
        :param sort: Sort results by ID, use 1 to sort asc, 2 for desc, default is no sort
        :param fields: specify fields to include in result 'lastname, firstname, email'
        :return: Dictionary of user's with each page of response corresponding to key,
        1,2,etc
        """
        count = 0
        next_page = 1
        response = {}
        original_user_base_url = user.base_url
        while next_page != 0:
            if sort == 0:
                r = user.session.get(user.base_url + user.user_endpoint + ('?' if  '?' not in user.user_endpoint else '&') +
                                     '&fields=%s' % str(fields), verify=False)
            elif sort == 1:
                r = user.session.get(user.base_url + user.user_endpoint + ('?' if  '?' not in user.user_endpoint else '&') +
                                     'sort=id&fields=%s' % str(fields), verify=False)
            else:
                r = user.session.get(user.base_url + user.user_endpoint + ('?' if  '?' not in user.user_endpoint else '&') +
                                     'sort=-id&fields=%s' % str(fields), verify=False)
            if r.status_code != 200:
                print user.handle_error(**{'status_code':r.status_code,
                                           'message_body':r.text,
                                           'url': user.base_url + user.user_endpoint,
                                           'headers':user.session.headers})
                next_page == 0
                return False
            else:
                if r.json()['pagination']['next_link'] == None:
                    next_page == 0
                    response[count] = r.json()
                    return response
                else:
                    user.user_endpoint = original_user_base_url + '?after_cursor=' + r.json()['pagination']['after_cursor']
                    response[count] = r.json()
                    count += 1

    def get_user_by_id(user, id):
        r = user.session.get(user.base_url + user.user_endpoint + '/%s' % str(id), verify=False)
        if r.status_code != 200:
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.target + '/token',
                                       'headers':user.session.headers})
            return False
        else:
            return r.json()

    def get_apps_for_user(user, id):
        r = user.session.get(user.base_url + user.user_endpoint + '/%s/apps' % str(id), verify=False)
        if r.status_code != 200:
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.base_url + user.user_endpoint,
                                       'headers':user.session.headers})
            exit()
        else:
            return r.json()

    def get_roles_for_user(user, id):
        r = user.session.get(user.base_url + user.user_endpoint + '/%s/roles' % str(id), verify=False)
        if r.status_code != 200:
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.base_url + user.user_endpoint,
                                       'headers':user.session.headers})
            exit()
        else:
            return r.json()

    def get_custom_attributes(user):
        r = user.session.get(user.base_url + user.user_endpoint + '/custom_attributes', verify=False)
        if r.status_code != 200:
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.base_url + user.user_endpoint,
                                       'headers':user.session.headers})
            exit()
        else:
            return r.json()

    def user_exists(user,email):
        r = user.session.get(user.base_url + user.user_endpoint + '?email=%s&fields=id,email,username' % email)
        if 'email' not in r.content:
            return False
        else:
            return True
	
	###
	def user_exists_by_username(user,username):
		r = user.session.get(user.base_url + user.user_endpoint + '?username=%s&fields=id,email,username' % username)
		if 'username' not in r.content:
			return False
		else:
			return True


    def search_users(user,
                     s_field='',
                     s_string='',
                     sort=False,
                     r_sort=False,
                     since='',
                     until='',
                     fields=''):
        """
        Search for Users
        :param s_field: search field (ex. email)
        :param s_string: search query (ex. *@onelogin.com)
        :param sort: Enable sorting by ID (True/False)
        :param r_sort: Sort by ID in reverse (True/False)
        :param since: Example: 2016-01-01T00:00:00.001Z
        :param until: Example: 2016-03-01T00:00:00.001Z
        :param fields: fields in response (Ex. firstname, email, username)
        :return:
        """
        count = 0
        next_page = True
        response = {}
        original_user_base_url = user.base_url
        while next_page:
            if not sort and not r_sort:
                search_terms = str(s_field) + '=' + str(s_string) + '&fields=' + str(fields) + '&since=' + str(since) + '&until=' + str(until)
                r = user.session.get((user.base_url + user.user_endpoint + ('?' if  '?' not in user.user_endpoint else '&') + search_terms), verify=False)
            elif sort and not r_sort:
                search_terms = 'sort=id&' + str(s_field) + '=' + str(s_string) + \
                               '&fields=' + str(fields) + '&since=' + str(since) + \
                               '&until=' + str(until)
                r = user.session.get(user.base_url +
                                     user.user_endpoint +
                                     ('?' if  '?' not in user.user_endpoint else '&') +
                                     str(search_terms))
            elif sort and r_sort:
                search_terms = ('sort=-id&' + str(s_field) + '=' + str(s_string) +
                                '&fields=' + str(fields) + '&since=' + str(since) +
                                '&until=' + str(until))
                r = user.session.get(user.base_url +
                                     user.user_endpoint +
                                     ('?' if  '?' not in user.user_endpoint else '&') +
                                     str(search_terms))
            elif not sort and r_sort:
                search_terms = 'sort=-id&' + str(s_field) + '=' + str(s_string) + \
                               '&fields=' + str(fields) + '&since=' + str(since) + \
                               '&until=' + str(until)
                r = user.session.get(user.base_url +
                                     user.user_endpoint +
                                     ('?' if  '?' not in user.user_endpoint else '&') +
                                     str(search_terms))

            if r.status_code != 200:
                print user.handle_error(**{'status_code':r.status_code,
                                           'message_body':r.text,
                                           'url': user.base_url + user.user_endpoint,
                                           'headers':user.session.headers})
                return False
            else:
                if r.json()['pagination']['next_link'] == None:
                    user.next_page = False
                    response[count] = r.json()
                    return response
                else:
                    user.user_endpoint = original_user_base_url + '?after_cursor=' + r.json()['pagination']['after_cursor']
                    print "..searching....page = {0}".format(count)
                    response[count] = r.json()
                    count += 1

    def create_user(user, **kwargs):
        """
        Create a user via the API, will not update custom attributes (use
        set_user_custom_attributes)
        :param kwargs: required: firstname, lastname, email, username -- optional:
        directory_id, distinguished_name, external_id, group_id, invalid_login_attempts,
        locale_code, manager_ad_id, member_of, notes, openid_name, phone, samaccountname,
        userprincipalname
        :return:
        """
        if 'firstname' not in kwargs:
            raise ValueError('firstname value is required to create user')
        if 'lastname' not in kwargs:
            raise ValueError('lastname is required to create user')
        if 'username' not in kwargs:
            raise ValueError('username is required to create user')
        if 'email' not in kwargs:
            raise ValueError('email is required to create user')
        payload = {}
        for k,v in kwargs.iteritems():
            payload[k] = v
        r = user.session.post(user.base_url + user.user_endpoint, json=payload)
        if r.status_code not in (200,201):
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.base_url + user.user_endpoint,
                                       'headers':user.session.headers,
                                       'payload':payload})
            return False
        else:
            return r.json()

    def create_session_login_token(user, username_or_email, password, subdomain, return_to_url='', ip_address='', browser_id=''):
        """
        Create login onelogin_session token for use with other applications and user login
        :param username_or_email: testuser@acme.com
        :param password: 12345
        :param subdomain: testcorp
        :param return_to_url: //NOT IMPLEMENTED//
        :param ip_address: //NOT IMPLEMENTED//
        :param browser_id: //NOT IMPLEMENTED//
        :return: dictionary that contains session_token
        """
        user.session_endpoint = '/api/1/login/auth'
        payload = {
            'username_or_email':username_or_email,
            'password':password,
            'subdomain':subdomain
        }
        r = user.session.post(user.base_url + user.session_endpoint, json=payload)
        if r.status_code != 200:
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.base_url + user.session_endpoint,
                                       'headers':user.session.headers,
                                       'payload':payload})
            return False
        else:
            return r.json()

    def update_user(user, id, **kwargs):
        """
        :param id:
        :param kwargs:
        :return:
        """
        payload = {}
        user.update_user_endpoint = '/api/1/users/%s' % id
        for k,v in kwargs.iteritems():
            payload[k] = v
        r = user.session.put(user.base_url + user.update_user_endpoint, json=payload)
        if r.status_code != 200:
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.base_url + user.update_user_endpoint,
                                       'headers':user.session.headers,
                                       'payload':payload})
            return False
        else:
            return r.json()

    def add_roles_to_user(user, id, role_id_array):
        """
        :param id:
        :param role_id_array:
        :return:
        """
        user.add_roles_endpoint = '/api/1/users/%s/add_roles' % id
        payload = {
            'role_id_array':role_id_array
        }
        r = user.session.put(user.base_url + user.add_roles_endpoint, json=payload)
        if r.status_code != 200:
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.base_url + user.add_roles_endpoint,
                                       'headers':user.session.headers,
                                       'payload':payload})
            return False
        else:
            return r.json()

    def remove_roles_from_user(user, id, role_id_array):
        """
        :param id:
        :param role_id_array:
        :return:
        """
        user.remove_roles_endpoint = '/api/1/users/%s/remove_roles' % id
        payload = {
            'role_id_array':role_id_array
        }
        r = user.session.put(user.base_url + user.remove_roles_endpoint, json=payload)
        if r.status_code != 200:
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.base_url + user.add_roles_endpoint,
                                       'headers':user.session.headers,
                                       'payload':payload})
            return False
        else:
            return r.json()

    def set_password_with_cleartext(user, id, password, password_confirmation):
        """
        :param id:
        :param password:
        :param confirmation:
        :return:
        """
        user.set_clear_password_endpoint = '/api/1/users/set_password_clear_text/%s' % id
        payload = {
            'password':password,
            'password_confirmation':password_confirmation
        }
        r = user.session.put(user.base_url + user.set_clear_password_endpoint, json=payload)
        if r.status_code != 200:
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.target + '/token',
                                       'headers':user.session.headers,
                                       'payload':payload})
            return False
        else:
            return r.json()

    def set_password_with_salt_sha256(user, id, password, password_confirmation,
                                      password_salt, password_algorithm='salt+sha256'):
        user.set_clear_password_endpoint = '/api/1/users/set_password_using_salt/%s' % id
        payload = {
            'password':password,
            'password_confirmation':password_confirmation,
            'password_algorithm':password_algorithm,
            'password_salt':password_salt
        }
        r = user.session.put(user.base_url + user.set_clear_password_endpoint, json=payload)
        if r.status_code != 200:
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.target + '/token',
                                       'headers':user.session.headers,
                                       'payload':payload})
            return False
        else:
            return r.json()

    def set_user_custom_attributes(user, id, **kwargs):
        """
        :param id:
        :param kwargs:
        :return:
        """
        user.update_attributes_endpoint = '/api/1/users/%s/set_custom_attributes' % id
        payload = {}
        for k,v in kwargs.iteritems():
            payload[k] = v
        r = user.session.put(user.base_url + user.update_attributes_endpoint, json=payload)
        if r.status_code != 200:
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.target + '/token',
                                       'headers':user.session.headers,
                                       'payload':payload})
            return False
        else:
            return r.json()

    def log_user_out(user, id):
        """
        :return:
        """
        user.log_user_out_endpoint = '/api/1/users/%s/logout' % id
        r = user.session.put(user.base_url + user.log_user_out_endpoint)
        if r.status_code != 200:
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.target + '/token',
                                       'headers':user.session.headers,
                                       'payload':payload})
            return False
        else:
            return r.json()

    def lock_user(user, id, locked_until=0):
        """
        :param id:
        :param locked_until:
        :return:
        """
        user.lock_user_endpoint = '/api/1/users/%s/lock_user' % id
        r = user.session.put(user.base_url + user.lock_user_endpoint,
                             json={'locked_until':locked_until})
        if r.status_code != 200:
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.target + '/token',
                                       'headers':user.session.headers,
                                       'payload':payload})
            return False
        else:
            return r.json()

    def delete_user(user, id):
        """
        Delete an existing user
        :return:
        """
        user.user_delete_endpoint = '/api/1/users/%s' % id
        r = user.session.delete(user.base_url + user.user_delete_endpoint)
        if r.status_code != 200:
            print user.handle_error(**{'status_code':r.status_code,
                                       'message_body':r.text,
                                       'url': user.target + '/token',
                                       'headers':user.session.headers,
                                       'payload':payload})
            return False
        else:
            return r.json()


class Role(Token):
    """
    TODO: Call Role API to list, create, destory, update, and search Roles
    """

    def __init__(role, token):
        """
        TODO: Initialize the Role Object
        :return:
        """
        role.session = requests.session()
        role.session.headers = {'Content-Type': 'application/json'}
        role.roles_endpoint = '/api/1/roles'
        try:
            role.base_url = token.base_url
            role.session.headers.update({'Authorization': 'Bearer:%s' % token.access_token})
        except:
            raise ValueError('Token not found, have you initialized the Token yet?')

    def get_roles(role, id=0, name=0):
        """
        :return:
        """
        r = role.session.get(role.base_url + role.roles_endpoint + '?%s%s' %
                             ('&id=' + str(id),'&name=' + str(name)))
        if r.status_code != 200:
            print role.handle_error(**{
                'status_code':r.status_code,
                'message_body':r.text,
                'url': role.base_url +
                       role.roles_endpoint +
                      '?%s%s' % ('&id=' + str(id), '&name=' + str(name)),
                'headers':role.session.headers})
            exit()
        else:
            return r.json()


class Group(Token):
    """
    TODO: Call Group API to list, create, destory, and search roles
    """

    def __init__(group, token):
        """
        TODO: Initialize the Group Object
        :return:
        """
        group.session = requests.session()
        group.session.headers = {'Content-Type': 'application/json'}
        group.group_endpoint = '/api/1/groups'
        try:
            group.base_url = token.base_url
            group.session.headers.update({'Authorization': 'Bearer:%s' % token.access_token})
        except:
            raise ValueError('Token not found, have you initialized the Token yet?')

    def create_group(self):
        """
        TODO: Create a new Group
        :return:
        """

    def update_group(self):
        """
        TODO: Update an existing Group
        :return:
        """

    def delete_group(self):
        """
        TODO: Delete an existing Group
        :return:
        """

    def search_group(self):
        """
        TODO: Search for an existing Group
        """


class Events(Token):
    """
    TODO: Events
    """

    def __init__(events, token):
        events.session = requests.session()
        events.session.headers = {'Content-Type': 'application/json'}
        events.events_endpoint = '/api/1/events'
        try:
            events.base_url = token.base_url
            events.session.headers.update({'Authorization': 'Bearer:%s' % token.access_token})
        except:
            raise ValueError('Token not found, have you initialized the Token yet?')

    def get_events(events, query=''):
        """
        :param query:
        :return:
        """
        events.query = query[1:] if query.startswith("?") or query.startswith("&") else query
        count = 0
        response = {}
        events.next_page = True
        original_event_base_url = events.events_endpoint
        while events.next_page:
            r = events.session.get(events.base_url + events.events_endpoint + ('?' if  '?' not in events.events_endpoint else '&') + events.query, verify=False)
            if r.json()['pagination']['next_link'] == None:
                events.next_page = False
                response[count] = r.json()
                return response
            else:
                events.events_endpoint =  original_event_base_url + '?after_cursor=' + r.json()['pagination']['after_cursor']
                print "..searching....page = {0}".format(count)
                response[count] = r.json()
                count += 1

    def search_events(events, **kwargs):
        query = ''
        for key in ('client_id', 'client_secret', 'directory_id', 'event_type_id', 'id',
                    'resolution', 'since', 'until', 'user_id'):
            if key in kwargs:
                query += '&%s=%s' % (key, kwargs[key])
        if query.startswith("&"):
            query = query[1:]
        result = events.get_events(query)
        return result
