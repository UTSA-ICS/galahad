import sys
from flask import request, Response

from flask import Blueprint, url_for
from flask import abort, redirect, render_template
from authlib.flask.oauth2 import current_token
from ..auth import require_login
from ..models import OAuth2Client, User
from ..forms.client import (Client2Form, OAuth2ClientWrapper)
from ..ldaplookup import LDAP
from ..apiendpoint import EndPoint
from ..apiendpoint_admin import EndPoint_Admin
from ..apiendpoint_security import EndPoint_Security
from ..services.oauth2 import require_oauth
from ..services.errorcodes import ErrorCodes
import json
import time

from ..services.oauth2 import require_oauth
from ..services.errorcodes import ErrorCodes
from authlib.flask.oauth2 import current_token

bp = Blueprint('virtue', __name__)


def get_endpoint():
    inst = LDAP( '', '' )
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s( dn, 'Test123!' )

    ep = EndPoint('jmitchell@virtue.com', 'Test123!')
    ep.inst = inst

    return ep


def get_admin_endpoint():
    inst = LDAP( '', '' )
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s( dn, 'Test123!' )

    epa = EndPoint_Admin('jmitchell@virtue.com', 'Test123!')
    epa.inst = inst

    return epa


def get_security_endpoint():
    inst = LDAP( '', '' )
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s( dn, 'Test123!' )

    eps = EndPoint_Security('jmitchell@virtue.com', 'Test123!')
    eps.inst = inst

    return eps


def make_response(message):

    result = ErrorCodes.user['unspecifiedError']

    try:
        # Will throw an error if message is not a real json, or the result is a failure
        result = json.loads(message)
        if (type(result) == dict):
            assert result.get('status', 'success') != 'failed'

        response = Response(message, status=200, mimetype='application/json')

    except Exception as e:

        response = Response(
            json.dumps(result['result']),
            status=400,
            mimetype='application/json')

        response.headers['status'] = 'failed'

    return response


def get_user():

    user = User.query.filter_by(id=current_token.user_id).first()
    user = user.email.replace('@virtue.com', '')

    return user


################ User API ##################


@bp.route('/user/role/get', methods=['GET'])
@require_oauth()
def role_get():

    role = ''

    try:
        # Information about the indicated Role. Type: Role
        ep = get_endpoint()
        role = ep.role_get(get_user(), request.args['roleId'])

        return make_response(role)

    except:
        print("Unexpected error:", sys.exc_info())
        return make_response(role)


@bp.route('/user/role/list', methods=['GET'])
@require_oauth()
def user_role_list():

    roleList = ''

    try:
        # A set of Roles available to the given User. Type: set of Role
        ep = get_endpoint()
        roleList = ep.user_role_list(get_user())

        return make_response(roleList)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(roleList)


@bp.route('/user/virtue/list', methods=['GET'])
@require_oauth()
def user_virtue_list():

    virtueList = ''

    try:
        # A set of Virtues for the given User. Type: set of Virtue.
        ep = get_endpoint()
        virtueList = ep.user_virtue_list(get_user())

        return make_response(virtueList)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(virtueList)


@bp.route('/user/virtue/get', methods=['GET'])
@require_oauth()
def virtue_get():

    virtueId = ''

    try:
        # Information about the indicated Virtue. Type: Virtue.
        ep = get_endpoint()
        virtueId = ep.virtue_get(get_user(), request.args['virtueId'])

        return make_response(virtueId)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(virtueId)


@bp.route('/user/virtue/create', methods=['GET'])
@require_oauth()
def virtue_create():

    roleId = ''

    try:
        # Information about the created Virtue. Type: Virtue
        ep = get_endpoint()
        roleId = ep.virtue_create(get_user(), request.args['roleId'])

        return make_response(roleId)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(roleId)


@bp.route('/user/virtue/launch', methods=['GET'])
@require_oauth()
def virtue_launch():

    virtue = ''

    try:
        # Information about the launched Virtue. Type: Virtue
        ep = get_endpoint()
        virtue = ep.virtue_launch(get_user(), request.args['virtueId'])

        return make_response(virtue)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(virtue)


@bp.route('/user/virtue/stop', methods=['GET'])
@require_oauth()
def virtue_stop():

    virtue = ''

    try:
        # Information about the stopped Virtue. Type: Virtue
        ep = get_endpoint()
        virtue = ep.virtue_stop(get_user(), request.args['virtueId'])

        return make_response(virtue)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(virtue)


@bp.route('/user/virtue/destroy', methods=['GET'])
@require_oauth()
def virtue_destroy():

    ret = ''

    try:
        # Destroys a Virtue. Releases all resources.
        ep = get_endpoint()
        ret = ep.virtue_destroy(get_user(), request.args['virtueId'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/user/application/get', methods=['GET'])
@require_oauth()
def application_get():

    application = ''

    try:
        # The Application with the given ID. Type: Application
        ep = get_endpoint()
        application = ep.application_get(get_user(), request.args['appId'])

        return make_response(application)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(application)


@bp.route('/user/virtue/application/launch', methods=['GET'])
@require_oauth()
def virtue_application_launch():

    application = ''

    try:
        # Information about the launched Application. Format is implementation-specific.
        # Type: object

        ep = get_endpoint()
        application = ep.virtue_application_launch(
            get_user(), request.args['virtueId'], request.args['appId'])
        return make_response(application)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(application)


@bp.route('/user/virtue/application/stop', methods=['GET'])
@require_oauth()
def virtue_application_stop():

    ret = ''

    try:
        # Stops a running Application in the indicated Virtue.
        ep = get_endpoint()
        ret = ep.virtue_application_stop(get_user(), request.args['virtueId'],
                                         request.args['appId'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/test', methods=['GET'])
@require_login
def virtue_test():

    test = ''

    for arg in request.args:
        test += arg + ':' + request.args[arg] + '&'

    return test


################ Admin API ##################


@bp.route('/admin/application/list', methods=['GET'])
@require_oauth()
def admin_application_list():

    ret = ''

    try:
        # Lists all Applications currently available in the system.
        ep = get_admin_endpoint()
        ret = ep.application_list()

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/resource/get', methods=['GET'])
@require_oauth()
def admin_resource_get():

    ret = ''

    try:
        # Gets information about the indicated Resource.
        ep = get_admin_endpoint()
        ret = ep.resource_get(request.args['resourceId'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/resource/list', methods=['GET'])
@require_oauth()
def admin_resource_list():

    ret = ''

    try:
        # Lists all Resources currently available in the system.
        ep = get_admin_endpoint()
        ret = ep.resource_list()

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/resource/attach', methods=['GET'])
@require_oauth()
def admin_resource_attach():

    ret = ''

    try:
        # Attaches the indicated Resource to the indicated Virtue.
        # Does not change the underlying Role.
        ep = get_admin_endpoint()
        ret = ep.resource_attach(request.args['resourceId'],
                                 request.args['virtueId'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/resource/detach', methods=['GET'])
@require_oauth()
def admin_resource_detach():

    ret = ''

    try:
        # Detaches the indicated Resource from the indicated Virtue.
        # Does not change the underlying Role.
        ep = get_admin_endpoint()
        ret = ep.resource_detach(request.args['resourceId'],
                                 request.args['virtueId'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/role/create', methods=['GET'])
@require_oauth()
def admin_role_create():

    ret = ''

    try:
        # Creates a new Role with the given parameters.
        ep = get_admin_endpoint()
        ret = ep.role_create(json.loads(request.args['role']))

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/role/list', methods=['GET'])
@require_oauth()
def admin_role_list():

    ret = ''

    try:
        # Lists all Roles currently available in the system.
        ep = get_admin_endpoint()
        ret = ep.role_list()

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/system/export', methods=['GET'])
@require_oauth()
def admin_system_export():

    ret = ''

    try:
        # Export the Virtue system to a file.
        ep = get_admin_endpoint()
        ret = ep.system_export()

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/system/import', methods=['GET'])
@require_oauth()
def admin_system_import():

    ret = ''

    try:
        # Import the Virtue system from the input bytestream data.
        ep = get_admin_endpoint()
        ret = ep.system_import(request.args['data'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/test/import/user', methods=['GET'])
@require_oauth()
def admin_test_import_user():

    ret = ''

    try:
        # Imports a pre-defined User that will be used for testing.
        # If called multiple times for the same User, the same username should
        # be returned.
        ep = get_admin_endpoint()
        ret = ep.test_import_user(request.args['which'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/test/import/application', methods=['GET'])
@require_oauth()
def admin_test_import_application():

    ret = ''

    try:
        # Imports a pre-defined Application that will be used for testing.
        # If called multiple times for the same Application, the same ID
        # should be returned.
        ep = get_admin_endpoint()
        ret = ep.test_import_application(request.args['which'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/test/import/role', methods=['GET'])
@require_oauth()
def admin_test_import_role():

    ret = ''

    try:
        # Imports a pre-defined Role that will be used for testing.
        # If called multiple times for the same Role, the same ID should be returned.
        ep = get_admin_endpoint()
        ret = ep.test_import_role(request.args['which'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/user/list', methods=['GET'])
@require_oauth()
def admin_user_list():

    ret = ''

    try:
        # Lists all Users currently present in the system.
        ep = get_admin_endpoint()
        ret = ep.user_list()

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/user/get', methods=['GET'])
@require_oauth()
def admin_user_get():

    ret = ''

    try:
        # Gets information about the indicated User.
        ep = get_admin_endpoint()
        ret = ep.user_get(request.args['username'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/user/virtue/list', methods=['GET'])
@require_oauth()
def admin_user_virtue_list():

    ret = ''

    try:
        # Lists the current Virtue instantiations for the given User.
        ep = get_admin_endpoint()
        ret = ep.user_virtue_list(request.args['username'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/user/role/authorize', methods=['GET'])
@require_oauth()
def admin_user_role_authorize():

    ret = ''

    try:
        # Authorizes the indicated Role for the given User.
        # This should also post a message to the User to let them know what happened.
        ep = get_admin_endpoint()
        ret = ep.user_role_authorize(request.args['username'],
                                     request.args['roleId'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


@bp.route('/admin/user/role/unauthorize', methods=['GET'])
@require_oauth()
def admin_user_role_unauthorize():

    ret = ''

    try:
        # Unauthorizes the indicated Role for the given User.
        ep = get_admin_endpoint()
        ret = ep.user_role_unauthorize(request.args['username'],
                                       request.args['roleId'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(ret)


################ Security API ##################


@bp.route('/security/api_config', methods=['GET'])
@require_oauth()
def security_api_config():

    ep = get_security_endpoint()

    try:

        ret = ep.set_api_config(request.args)

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(
            json.dumps(ErrorCodes.security['unspecifiedError']))


@bp.route('/security/transducer/list', methods=['GET'])
@require_oauth()
def transducer_list():

    ep = get_security_endpoint()

    try:

        ret = ep.transducer_list()

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(
            json.dumps(ErrorCodes.security['unspecifiedError']))


@bp.route('/security/transducer/get', methods=['GET'])
@require_oauth()
def transducer_get():

    ep = get_security_endpoint()

    if 'transducerId' not in request.args:
        return make_response('ERROR: Required arguments: transducerId')

    try:

        ret = ep.transducer_get(request.args['transducerId'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(
            json.dumps(ErrorCodes.security['unspecifiedError']))


@bp.route('/security/transducer/enable', methods=['GET'])
@require_oauth()
def transducer_enable():

    ep = get_security_endpoint()

    if 'transducerId' not in request.args or 'virtueId' not in request.args or 'configuration' not in request.args:
        return make_response(
            'ERROR: Required arguments: transducerId, virtueId, configuration')

    try:

        ret = ep.transducer_enable(request.args['transducerId'],
                                   request.args['virtueId'],
                                   request.args['configuration'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(
            json.dumps(ErrorCodes.security['unspecifiedError']))


@bp.route('/security/transducer/disable', methods=['GET'])
@require_oauth()
def transducer_disable():

    ep = get_security_endpoint()

    if 'transducerId' not in request.args or 'virtueId' not in request.args:
        return make_response(
            'ERROR: Required arguments: transducerId, virtueId')

    try:

        ret = ep.transducer_disable(request.args['transducerId'],
                                    request.args['virtueId'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(
            json.dumps(ErrorCodes.security['unspecifiedError']))


@bp.route('/security/transducer/get_enabled', methods=['GET'])
@require_oauth()
def transducer_get_enabled():

    ep = get_security_endpoint()

    if 'transducerId' not in request.args or 'virtueId' not in request.args:
        return make_response(
            'ERROR: Required arguments: transducerId, virtueId')

    try:

        ret = ep.transducer_get_enabled(request.args['transducerId'],
                                        request.args['virtueId'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(
            json.dumps(ErrorCodes.security['unspecifiedError']))


@bp.route('/security/transducer/get_configuration', methods=['GET'])
@require_oauth()
def transducer_get_configuration():

    ep = get_security_endpoint()

    if 'transducerId' not in request.args or 'virtueId' not in request.args:
        return make_response(
            'ERROR: Required arguments: transducerId, virtueId')

    try:

        ret = ep.transducer_get_configuration(request.args['transducerId'],
                                              request.args['virtueId'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(
            json.dumps(ErrorCodes.security['unspecifiedError']))


@bp.route('/security/transducer/list_enabled', methods=['GET'])
@require_oauth()
def transducer_list_enabled():

    ep = get_security_endpoint()

    if 'virtueId' not in request.args:
        return make_response('ERROR: Required arguments: virtueId')

    try:
        ret = ep.transducer_list_enabled(request.args['virtueId'])

        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(
            json.dumps(ErrorCodes.security['unspecifiedError']))
