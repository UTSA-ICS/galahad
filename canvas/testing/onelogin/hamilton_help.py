import sys
sys.path.insert(0, '../../lib/')

import requests

client_id = '116bb297f085318ac04833647705c4e329216a1d3a39a1189f515069a90c69be'
client_secret = 'dd25227ff84e68fbc2b5f3b0b8313162fdce6b33cc1827764c21c9922587d924'
shard = 'US'

creds = {'client_id':client_id, 'client_secret':client_secret, 'shard':shard}

class OneLogin(object):
	def __init__(self, shard='US'):
		#self.base_url = 'https://api.us.onelogin.com'			#
		self.base_url = 'http://hamilton:8000'

	def set_attributes(self, kwargs):
		for kwarg_key, kwarg_value in kwargs.iteritems():
			setattr(self, kwarg_key, kwarg_value)

	def handle_error(self, **kwargs):
		error = {}
		for k,v in kwargs.iteritems():
			error[k] = v
		return error


class Token(OneLogin):
	def __init__(token, **kwargs):
		for key in ('client_id', 'client_secret', 'shard'):
			if key in kwargs:
				setattr(token, key, kwargs[key])
		token.session = requests.session()
		token.session.headers = {'Content-Type': 'application/json'}
		oauth_endpoint = '/login'							#
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
		authorization = 'client_id: %s, client_secret: %s' % (token.client_id, token.client_secret)
		token.session.headers.update({'Authorization':authorization})
		r = token.session.post(token.target + '/token', verify=False, json={'grant_type':'client_credentials'})
		if r.status_code != 200:
			print token.handle_error(**{'status_code':r.status_code, 'message_body':r.text, 'url':token.target+'/token', 'headers':token.session.headers})
			return False
		else:
			print r.json()
			token.set_attributes({
				'access_token':r.json()['data'][0]['access_token'],
				'refresh_token':r.json()['data'][0]['refresh_token'],
				'token_created_at':r.json()['data'][0]['created_at'],
				'token_expires_at':r.json()['data'][0]['expires_in']})
			return True

	def refresh_the_token(token):
		r = token.session.post(token.target + '/token', verify=False,
							   json={ 'grant_type':'refresh_token',
									  'refresh_token':token.refresh_token,
									  'access_token':token.access_token    })
		if r.status_code != 200:
			print token.handle_error(**{'status_code':r.status_code,
										'message_body':r.text,
										'url':token.target+'/token',
										'headers':token.session.headers})
			return False
		else:
			token.set_attributes({
				'access_token':r.json()['data'][0]['access_token'],
				'refresh_token':r.json()['data'][0]['refresh_token'],
				'created_at':r.json()['data'][0]['created_at'],
				'expires_in':r.json()['data'][0]['expires_in']		 })
			return True

	def revoke_the_token(token):
		r = token.session.post(token.target + '/revoke', verify=False,
							   json={ 'grant_type':'revoke_token',
									  'access_token':token.access_token,
									  'client_id':token.client_id,
									  'client_secret':token.client_secret  })
		if r.status_code != 200:
			print token.handle_error(**{'status_code':r.status_code,
										'message_body':r.text,
										'url':token.target+'/revoke',
										'headers':token.session.headers  })
			return False
		else:
			return True

	def check_token_expiration(self):
		""" todo """

	def check_rate_limit(token):
		if token.access_token:
			authorization = 'Bearer:%s' % token.access_token
			token.session.headers.update({'Authorization':authorization})
		else:
			return 'Access Token not found'
		r = token.session.get(token.base_url + '/auth/rate_limit', verify=False)
		if r.status_code != 200:
			print token.handle_error(**{'status_code':r.status_code,
										'message_body':r.text,
										'url':token.target+'/revoke',
										'headers':token.session.headers})
			return False
		else:
			return r
		

if __name__ == '__main__':
	token = Token(**creds)
	print token
