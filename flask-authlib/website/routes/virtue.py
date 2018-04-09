import sys
from flask import request, Response

from flask import Blueprint, url_for
from flask import abort, redirect, render_template
from authlib.flask.oauth2 import current_token
from ..auth import require_login
from ..models import OAuth2Client, User
from ..forms.client import (
    Client2Form, OAuth2ClientWrapper
)
from ..apiendpoint import EndPoint
from ..services.oauth2 import require_oauth
import json
import time
import aws

from ..services.oauth2 import require_oauth

bp = Blueprint('virtue', __name__)


def endpoint():
    return EndPoint( 'jmitchell@virtue.com', 'Test123!' )

def make_response(message, status):
    if status == 'success':
        response = Response("{'status':'success', 'message': " + message + " }", status=200, mimetype='application/json')
        response.headers['status'] = 'success'
    else:
        response = Response("{'status':'failed', 'message': " + message + " }", status=400, mimetype='application/json')
        response.headers['status'] = 'failed'
    return response

def get_user():
    user = User.query.filter_by(id=current_token.user_id).first()
    user = user.email.replace('@virtue.com', '')
    print user
    return user


@bp.route('/user/role/get', methods=['GET'])
@require_oauth()
def role_get():
    role = ''
    try :
        # Information about the indicated Role. Type: Role
        ep = endpoint()
        role = ep.role_get( get_user(), request.args['roleId'] )
        return make_response(role, 'success')
    except:
        print("Unexpected error:", sys.exc_info())
        return make_response(role, 'failed')


@bp.route('/user/role/list', methods=['GET'])
@require_oauth()
def user_role_list():
    roleList = ''
    try :
        # A set of Roles available to the given User. Type: set of Role
        ep = endpoint()
        roleList = ep.user_role_list( get_user() )
        return make_response(roleList, 'success')
    except:
        print("Unexpected error:", sys.exc_info())
        return make_response(roleList, 'failed')


@bp.route('/user/virtue/list', methods=['GET'])
@require_oauth()
def user_virtue_list():
    virtueList = ''
    try :
        # A set of Virtues for the given User. Type: set of Virtue.
        ep = endpoint()
        virtueList = ep.user_virtue_list( get_user() )
        return make_response(virtueList, 'success')
    except:
        print("Unexpected error:", sys.exc_info())
        return make_response(virtueList, 'failed')


@bp.route('/user/virtue/get', methods=['GET'])
@require_oauth()
def virtue_get():
    virtueId = ''
    try :
        # Information about the indicated Virtue. Type: Virtue.
        ep = endpoint()
        virtueId = ep.virtue_get( get_user(), request.args['virtueId'] )
        return make_response(virtueId, 'success')
    except:
        print("Unexpected error:", sys.exc_info())
        return make_response(virtueId, 'failed')


@bp.route('/user/virtue/create', methods=['GET'])
@require_oauth()
def virtue_create():
    roleId = ''
    try :
        # Information about the created Virtue. Type: Virtue
        ep = endpoint()
        roleId = ep.virtue_create( get_user(), request.args['roleId'] )
        return make_response(roleId, 'success')
    except:
        print("Unexpected error:", sys.exc_info())
        return make_response(roleId, 'failed')


@bp.route('/user/virtue/launch', methods=['GET'])
@require_oauth()
def virtue_launch():
    virtue = ''
    try:
        # Information about the launched Virtue. Type: Virtue
        ep = endpoint()
        virtue = ep.virtue_launch( get_user(), request.args['virtueId'] )
        return make_response( virtue, 'success' )
    except:
        print("Unexpected error:", sys.exc_info())
        return make_response( virtue, 'failed' )

@bp.route('/user/virtue/stop', methods=['GET'])
@require_oauth()
def virtue_stop():
    virtue = ''
    try:
        # Information about the stopped Virtue. Type: Virtue
        ep = endpoint()
        virtue = ep.virtue_stop( get_user(), request.args['virtueId'] )
        return make_response( virtue, 'success' )
    except:
        print("Unexpected error:", sys.exc_info())
        return make_response( virtue, 'failed' )

@bp.route('/user/virtue/destroy', methods=['GET'])
@require_oauth()
def virtue_destroy():
    ret = ''
    try:
        # Destroys a Virtue. Releases all resources.
        ep = endpoint()
        ret = ep.virtue_destroy( get_user(), request.args['virtueId'] )
        return make_response( ret, 'success' )
    except:
        print("Unexpected error:", sys.exc_info())
        return make_response( ret, 'failed' )

@bp.route('/user/application/get', methods=['GET'])
@require_oauth()
def application_get():
    application = ''
    try:
        # The Application with the given ID. Type: Application
        ep = endpoint()
        application = ep.application_get( get_user(), request.args['appId'] )
        return make_response( application, 'success' )
    except:
        print("Unexpected error:", sys.exc_info())
        return make_response( application, 'failed' )

@bp.route('/user/application/launch', methods=['GET'])
@require_oauth()
def virtue_application_launch():
    application = ''
    try:
        # Information about the launched Application. Format is implementation-specific. Type: object
        ep = endpoint()
        application = ep.virtue_application_launch( get_user(),
                                                    request.args['virtueId'],
                                                    request.args['appId'] )
        return make_response( application, 'success' )
    except:
        print("Unexpected error:", sys.exc_info())
        return make_response( application, 'failed' )

@bp.route('/user/application/stop', methods=['GET'])
@require_oauth()
def virtue_application_stop():
    ret = ''
    try:
        # Stops a running Application in the indicated Virtue.
        ep = endpoint()
        ret = ep.virtue_application_stop( get_user(),
                                          request.args['virtueId'],
                                          request.args['appId'] )
        return make_response( ret, 'success' )
    except:
        print("Unexpected error:", sys.exc_info())
        return make_response( ret, 'failed' )

@bp.route('/test', methods=['GET'])
@require_login
def virtue_test():
    test = ''
    for arg in request.args:
        test += arg + ':' + request.args[arg] + '&'
    return test

