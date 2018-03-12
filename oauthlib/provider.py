from flask import Flask
from flask import request
from flask_oauthlib.provider import OAuth2Provider

app = Flask(__name__)
oauth = OAuth2Provider(app)

@app.route('/api/user')
@oauth.require_oauth('email','username')
def user():
	return jsonify(request.oauth.user)

@oauth.after_request
def valid_after_request(valid, oauth):
	if oauth.user in black_list:
		return False, oauth
	return valid, oauth

@app.route('/oauth/authorize', methods=['GET','POST'])
@oauth.authorize_handler
def authorize(*args, **kwargs):
	print('/oauth/authorize')
	print(request.method)
	if request.method == 'GET':
		print('request method = GET')
		print('page render')
		# return render_template('oauthorize.html')

	confirm = request.form.get('confirm', 'no')
	return confirm == 'yes'

@oauth.before_request
def limit_client_request():
	client_id = request.values.get('client_id')
	if not client_id:
		return
	client = Client.get(client_id)
	if over_limit(client):
		return abort(403)

	track_request(client)

@oauth.clientgetter
def get_client(client_id):
	client = get_client_model(client_id)
	# client is an object
	return client

@oauth.grantgetter
def grant(client_id, code):
	return get_grant(client_id, code)

@oauth.grantsetter
def set_grant(client_id, code, request, *args, **kwargs):
	save_grant(client_id, code, request.user, request.scopes)

@oauth.invalid_response
def invalid_require_oauth(req):
	return jsonify(message=req.error_message), 401

# require_oauth = protects resource with specified scopes

@app.route('/oauth/revoke', methods=['POST'])
@oauth.revoke_handler
def revoke_token():
	pass

@app.route('/oauth/token', methods=['POST'])
@oauth.token_handler
def access_token():
	return None

@oauth.tokengetter
def bearer_token(access_token=None, refresh_token=None):
	if access_token:
		return get_token(access_token=access_token)
	if refresh_token:
		return get_token(refresh_token=refresh_token)
	return None

@oauth.tokensetter
def set_token(token, request, *args, **kwargs):
	save_token(token, request.client, request.user)

@oauth.usergetter
def get_user(username, password, client, request, *args, **kwargs):
	if not client.has_password_credential_permission:
		return None
	user = User.get_user_by_username(username)
	if not user.validate_password(password):
		return None

	return user

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
