import json

success = 0
invalidOrMissingParameters = 1
userNotAuthorized = 2
userTokenExpired = 3
invalidId = 10
virtueNotStopped = 11
serverDestroyError = 100
notImplemented = 254
unspecifiedError = 255

_descriptions = {
	success: 'success: Successfully completed operation.',
	invalidOrMissingParameters: 'ERROR invalidOrMissingParameters: Invalid or missing parameters.',
	userNotAuthorized: 'ERROR userNotAuthorized: The User is not authorized for this operation.',
	userTokenExpired: 'ERROR userTokenExpired: The provided UserToken has expired.  Refresh your session and try again.',
	invalidId: 'ERROR invalidId: The given ID is invalid.',
	virtueNotStopped: 'ERROR virtueNotStopped: The indicated Virtue is not stopped.  Please stop it and try again.',
	serverDestroyError: 'ERROR serverDestroyError: There was an unanticipated server error destroying the indicated Virtue.  Check user messages and server logs for more information.',
	notImplemented: 'ERROR notImplemented: This function has not been implemented.',
	unspecifiedError: 'ERROR unspecifiedError: An otherwise-unspecified error.  Check user messages and/or error logs for more information.'
}

def get_description(exit_code):
	if exit_code not in _descriptions:
		return 'ERROR: unknown exit code: ' + str(exit_code)
	else:
		return _descriptions[exit_code]

def get_response_error(exit_code, details=''):
	return json.dumps({'exit_code': exit_code,
		'description': get_description(exit_code),
		'details': details})

def get_response_success():
	return json.dumps({'exit_code': success,
		'description': get_description(success)})
