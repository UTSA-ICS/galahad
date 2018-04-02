from flask import request

from flask import Blueprint, url_for
from flask import abort, redirect, render_template
from ..auth import require_login, current_user
from ..models import OAuth2Client, User
from ..forms.client import (
    Client2Form, OAuth2ClientWrapper
)
import json
import time
import aws
from ..vars import LDAP_DATABASE_URI, AD_DATABASE_URI, LDAP_PROTOCOL_VERSION
from ..ldaplookup import LDAP

bp = Blueprint('virtue', __name__)

class Virtue:
        aws_state_to_virtue_state = {
        'pending': 'CREATING',
        'running': 'RUNNING',
        'shutting-down': 'DELETING',
        'terminated': 'STOPPED',
        'stopping': 'STOPPING',
        'stopped': 'STOPPED'
        }

        def __init__(self):
                self.id = ''
                self.username = ''
                self.roleId = ''
                self.applicationIds = []
                self.resourceIds = []
                self.transducerIds = []
                self.state = ''
                self.ipAddress = ''
                self.awsClient = aws.AWS()

        def get_json(self):
                return json.dumps({'id': self.id,
                        'username': self.username,
                        'roleId': self.roleId,
                        'applicationIds': self.applicationIds,
                        'resourceIds': self.resourceIds,
                        'transducerIds': self.transducerIds,
                        'state': self.state,
                        'ipAddress': self.ipAddress})

        def __repr__(self):
                return self.get_json()

        def __str__(self):
                return self.get_json()

@bp.route('/user/application/get', methods=['GET'])
@require_login
def application_get():
    print request.args['appId']
    user = User.query.filter_by(email=current_user.email).first()
    print current_user.conn
    print user.conn
    return 'The Application with the given ID. Type: Application.'

@bp.route('/user/role/get', methods=['GET'])
@require_login
def role_get():
    print request.args['roleId']
    return 'Information about the indicated Role. Type: Role'

# TODO
# user login (username, password)
# user logout

@bp.route('/user/user/rolelist', methods=['GET'])
@require_login
def user_role_list():
    return 'A set of Roles available to the given User. Type: set of Role'

@bp.route('/user/user/virtuelist', methods=['GET'])
@require_login
def user_virtue_list():
    return 'A set of Virtues for the given User. Type: set of Virtue.'

@bp.route('/user/virtue/get', methods=['GET'])
@require_login
def virtue_get():
    print request.args['virtId']
    return 'Information about the indicated Virtue. Type: Virtue.'

@bp.route('/user/virtue/create', methods=['GET'])
@require_login
def virtue_create():
    if 'roleId' not in request.args:
        return 'Missing argument: roleId'

    print request.args['roleId']
    virtue = Virtue()
    virtue.roleId = request.args['roleId']

    virtue.awsClient.instance_create()
    virtue.id = virtue.awsClient.id
    virtue.ipAddress = virtue.awsClient.ipAddress
    virtue.state = virtue.aws_state_to_virtue_state.get(virtue.awsClient.state, 'UNKNOWN')

    return virtue.get_json()

@bp.route('/user/virtue/launch', methods=['GET'])
@require_login
def virtue_launch():
    print request.args['virtId']
    return 'Information about the launched Virtue. Type: Virtue'

@bp.route('/user/virtue/stop', methods=['GET'])
@require_login
def virtue_stop():
    print request.args['virtId']
    return 'Information about the stopped Virtue. Type: Virtue'

@bp.route('/user/virtue/destroy', methods=['GET'])
@require_login
def virtue_destroy():
    print request.args['virtId']
    return '0'

@bp.route('/user/virtue/applicationlaunch', methods=['GET'])
@require_login
def virtue_application_launch():
    print request.args['virtId']
    print request.args['appId']
    return 'Information about the launched Application. Format is implementation-specific. Type: object'

@bp.route('/user/virtue/applicationstop', methods=['GET'])
@require_login
def virtue_application_stop():
    print request.args['virtId']
    print request.args['appId']
    return '0'

@bp.route('/test', methods=['GET'])
@require_login
def virtue_test():
    test = ''
    for arg in request.args:
        test += arg + ':' + request.args[arg] + '&'
    return test
