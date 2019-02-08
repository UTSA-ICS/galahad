import inspect
import json
import logging
import sys

from authlib.flask.oauth2 import current_token
from flask import Blueprint
from flask import request, Response

from ..apiendpoint import EndPoint
from ..apiendpoint_admin import EndPoint_Admin
from ..apiendpoint_security import EndPoint_Security
from ..auth import require_login
from ..ldaplookup import LDAP
from ..models import User
from ..services.errorcodes import ErrorCodes
from ..services.oauth2 import require_oauth

bp = Blueprint('virtue', __name__)


def get_endpoint():
    inst = LDAP( '', '' )
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()

    #TODO: Remove hardcoded password
    inst.conn.simple_bind_s( dn, 'Test123!' )

    #TODO: Remove hardcoded credentials
    ep = EndPoint('slapd@virtue.gov', 'Test123!')
    ep.inst = inst

    return ep


def get_admin_endpoint():
    inst = LDAP( '', '' )
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    #TODO: Remove hardcoded password
    inst.conn.simple_bind_s( dn, 'Test123!' )

    #TODO: Remove hardcoded credentials
    epa = EndPoint_Admin('slapd@virtue.gov', 'Test123!')
    epa.inst = inst

    return epa


def get_security_endpoint():
    inst = LDAP( '', '' )
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    #TODO: Remove hardcoded password
    inst.conn.simple_bind_s( dn, 'Test123!' )

    #TODO: Remove hardcoded credentials
    eps = EndPoint_Security('slapd@virtue.gov', 'Test123!')
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
    user = user.email.split("@")[0]

    return user

def get_logger():
    try:
        logger = logging.getLogger('elasticLog')
        return logger
    except:
        return None


# func_name is included as a parameter because the logging framework will otherwise only report that
# this method was the logging function, which isn't very useful.  We pass the inspect.currentFrame()
# call instead of calling inspect.stack() here for performance reasons.
def log_to_elasticsearch(msg, extra, ret, func_name):
    extra['real_func_name'] = func_name
    try:
        response = json.loads(ret)
        if (response['status'] == 'success'):
            get_logger().info(msg, extra=extra)
        else:
            # Get result code
            extra['errorCode'] = response.result[0]
            # Get result message
            extra['errorMessage'] = response.result[1]
            get_logger().error(msg, extra=extra)
    # Response can be a large number of possible objects, so if ignore if it's not of the form of an error code
    except:
        get_logger().info(msg, extra=extra)


################ User API ##################


@bp.route('/user/role/get', methods=['GET'])
@require_oauth()
def role_get():

    role = ''

    try:
        # Information about the indicated Role. Type: Role
        ep = get_endpoint()
        role = ep.role_get(get_user(), request.args['roleId'])
        log_to_elasticsearch('Get role', extra={'user': get_user(), 'role_id': request.args['roleId']},
                             ret=role, func_name=inspect.currentframe().f_code.co_name)


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
        log_to_elasticsearch('Get role list', extra={'user': get_user()}, ret=roleList, func_name=inspect.currentframe().f_code.co_name)

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
        log_to_elasticsearch('Get virtue list', extra={'user': get_user()}, ret=virtueList, func_name=inspect.currentframe().f_code.co_name)


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
        log_to_elasticsearch('Get virtue', extra={'user': get_user(), 'virtue_id': request.args['virtueId']}, ret=virtueId, func_name=inspect.currentframe().f_code.co_name)

    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(virtueId)


@bp.route('/user/virtue/launch', methods=['GET'])
@require_oauth()
def virtue_launch():

    virtue = ''

    try:
        # Information about the launched Virtue. Type: Virtue
        ep = get_endpoint()
        virtue = ep.virtue_launch(get_user(), request.args['virtueId'])
        log_to_elasticsearch('Launch virtue', extra={'user': get_user(), 'virtue_id': request.args['virtueId']}, ret=virtue, func_name=inspect.currentframe().f_code.co_name)


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
        log_to_elasticsearch('Stop virtue', extra={'user': get_user(), 'virtue_id': request.args['virtueId']}, ret=virtue, func_name=inspect.currentframe().f_code.co_name)


    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(virtue)


@bp.route('/user/application/get', methods=['GET'])
@require_oauth()
def application_get():

    application = ''

    try:
        # The Application with the given ID. Type: Application
        ep = get_endpoint()
        application = ep.application_get(get_user(), request.args['appId'])
        log_to_elasticsearch('Get application', extra={'user': get_user(), 'app_id': request.args['appId']}, ret=application, func_name=inspect.currentframe().f_code.co_name)

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
            get_user(),
            request.args['virtueId'],
            request.args['appId'])
        log_to_elasticsearch('Launch virtue application', extra={'user': get_user(),
                                                                 'virtue_id': request.args['virtueId'],
                                                                 'app_id': request.args['appId']},
                             ret=application, func_name=inspect.currentframe().f_code.co_name)

    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(application)


@bp.route('/user/virtue/application/stop', methods=['GET'])
@require_oauth()
def virtue_application_stop():

    ret = ''

    try:
        ep = get_endpoint()
        ret = ep.virtue_application_stop(
            get_user(),
            request.args['virtueId'],
            request.args['appId'])
        log_to_elasticsearch('Stop virtue application', extra={'user': get_user(), 'virtue_id':
            request.args['virtueId'],
                                                              'app_id': request.args['appId']},
                             ret=ret, func_name=inspect.currentframe().f_code.co_name)


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
        ep = get_admin_endpoint()
        ret = ep.application_list()
        log_to_elasticsearch('Get admin application list', extra={'user': get_user()}, ret=ret, func_name=inspect.currentframe().f_code.co_name)

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
        log_to_elasticsearch('Get admin resource', extra={'user': get_user(), 'resource_id': request.args['resourceId']}, ret=ret, func_name=inspect.currentframe().f_code.co_name)



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
        log_to_elasticsearch('Get admin resource list', extra={'user': get_user()}, ret=ret, func_name=inspect.currentframe().f_code.co_name)


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
        ret = ep.resource_attach(
            request.args['resourceId'],
            request.args['virtueId'])
        log_to_elasticsearch('Attach admin resource',
                             extra={'user': get_user(), 'virtue_id': request.args['virtueId'],
                                    'resource_id': request.args['resourceId']}, ret=ret,
                             func_name=inspect.currentframe().f_code.co_name)

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
        ret = ep.resource_detach(
            request.args['resourceId'],
            request.args['virtueId'])
        log_to_elasticsearch('Detach admin resource',
                             extra={'user': get_user(), 'virtue_id': request.args['virtueId'],
                                    'resource_uid': request.args['resourceId']},
                             ret=ret, func_name=inspect.currentframe().f_code.co_name)

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

        # If UnitySize is not provided then set to default of 8GB
        unitySize = request.args.get('unitySize', '8GB')

        ret = ep.role_create(
            json.loads(request.args['role']),
            unity_img_name=unitySize)
        log_to_elasticsearch('Create admin role',
                             extra={'user': get_user(), 'role_id': request.args['role']}, ret=ret,
                             func_name=inspect.currentframe().f_code.co_name)

    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(ret)

@bp.route('/admin/role/destroy', methods=['GET'])
@require_oauth()
def admin_role_destroy():

    ret = ''

    try:
        # Destroys a role. Releases all resources.
        ep = get_admin_endpoint()
        ret = ep.role_destroy(request.args['roleId'])
        log_to_elasticsearch('Destroy role', extra={'user': get_user(), 'role_id': request.args['roleId']}, ret=ret,
                             func_name=inspect.currentframe().f_code.co_name)


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
        log_to_elasticsearch('Get admin role list', extra={'user': get_user()}, ret=ret, func_name=inspect.currentframe().f_code.co_name)


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
        log_to_elasticsearch('Export virtue to file', extra={'user': get_user()}, ret=ret, func_name=inspect.currentframe().f_code.co_name)


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
        log_to_elasticsearch('Import virtue from file', extra={'user': get_user()}, ret=ret, func_name=inspect.currentframe().f_code.co_name)


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
        log_to_elasticsearch('Get user list', extra={'user': get_user()}, ret=ret, func_name=inspect.currentframe().f_code.co_name)


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
        log_to_elasticsearch('Admin get user', extra={'user': get_user(), 'requested_username': request.args['username']}, ret=ret, func_name=inspect.currentframe().f_code.co_name)

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
        log_to_elasticsearch('Get virtue list for user', extra={'user': get_user(), 'requested_username': request.args['username']}, ret=ret, func_name=inspect.currentframe().f_code.co_name)


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
        ret = ep.user_role_authorize(
            request.args['username'],
            request.args['roleId'])
        log_to_elasticsearch('Authorize role for user',
                             extra={'user': get_user(),
                                    'requested_username': request.args['username'],
                                    'role_id': request.args['roleId']}, ret=ret,
                             func_name=inspect.currentframe().f_code.co_name)

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
        ret = ep.user_role_unauthorize(
            request.args['username'],
            request.args['roleId'])
        log_to_elasticsearch('Deauthorize role for user',
                             extra={'user': get_user(),
                                    'requested_username': request.args['username'],
                                    'role_id': request.args['roleId']},
                             ret=ret, func_name=inspect.currentframe().f_code.co_name)


    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(ret)


@bp.route('/admin/virtue/create', methods=['GET'])
@require_oauth()
def admin_virtue_create():

    roleId = ''

    try:
        # Information about the created Virtue. Type: Virtue
        ep = get_admin_endpoint()
        roleId = ep.virtue_create(request.args['username'], request.args['roleId'])
        log_to_elasticsearch('Create virtue', extra={'user': get_user(), 'requested_username': request.args['username'],
                                                            'role_id': request.args['roleId']},
                             ret=roleId, func_name=inspect.currentframe().f_code.co_name)


    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(roleId)


@bp.route('/admin/virtue/destroy', methods=['GET'])
@require_oauth()
def admin_virtue_destroy():

    ret = ''

    try:
        # Destroys a Virtue. Releases all resources.
        ep = get_admin_endpoint()
        ret = ep.virtue_destroy(request.args['virtueId'])
        log_to_elasticsearch('Destroy virtue', extra={'user': get_user(), 'virtue_id': request.args['virtueId']}, ret=ret, func_name=inspect.currentframe().f_code.co_name)


    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(ret)


@bp.route('/admin/galahad/get/id', methods=['GET'])
@require_oauth()
def admin_galahad_get_id():

    ret = ''

    try:
        # Outputs this Galahad system's ID
        ep = get_admin_endpoint()
        ret = ep.galahad_get_id()
        log_to_elasticsearch('Get Galahad ID', extra={'user': get_user()}, ret=ret, func_name=inspect.currentframe().f_code.co_name)

    except:
        print("Unexpected error: " + sys.exc_info())

    return make_response(ret)


@bp.route('/admin/application/add', methods=['GET'])
@require_oauth()
def admin_application_add():

    ret = ''

    try:
        ep = get_admin_endpoint()
        ret = ep.application_add(json.loads(request.args['application']))
        log_to_elasticsearch('Application add', extra={'user': get_user(), 'username': request.args['username'], 'application': request.args['application']}, ret=ret, func_name=inspect.currentframe().f_code.co_name)

    except:

        print("Unexpected error:", sys.exc_info())

    return make_response(ret)


################ Security API ##################


@bp.route('/security/api_config', methods=['GET'])
@require_oauth()
def security_api_config():

    ep = get_security_endpoint()

    try:

        ret = ep.set_api_config(json.loads(request.args['configuration']))
        log_to_elasticsearch('Get security config', extra={'user': get_user(), 'configuration': request.args['configuration']}, ret=ret, func_name=inspect.currentframe().f_code.co_name)
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
        log_to_elasticsearch('Get transducer list', extra={'user': get_user()}, ret=ret, func_name=inspect.currentframe().f_code.co_name)
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
        log_to_elasticsearch('Get transducer', extra={'user': get_user(), 'transducer_id': request.args['transducerId']}, ret=ret, func_name=inspect.currentframe().f_code.co_name)
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
        log_to_elasticsearch('Enable transducer', extra={'user': get_user(), 'transducer_id': request.args['transducerId'],
                                                            'virtue_id': request.args['virtueId'], 'configuration': request.args['configuration']}, ret=ret, func_name=inspect.currentframe().f_code.co_name)
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
        log_to_elasticsearch('Transducer disable', extra={'user': get_user(), 'transducer_id': request.args['transducerId'],
                                                            'virtue_id': request.args['virtueId']}, ret=ret, func_name=inspect.currentframe().f_code.co_name)
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
        log_to_elasticsearch('Get enabled transducers', extra={'user': get_user(), 'transducer_id': request.args['transducerId'],
                                                            'virtue_id': request.args['virtueId']}, ret=ret, func_name=inspect.currentframe().f_code.co_name)
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
        log_to_elasticsearch('Get transducer configuration', extra={'user': get_user(), 'transducer_id': request.args['transducerId'],
                                                            'virtue_id': request.args['virtueId']}, ret=ret, func_name=inspect.currentframe().f_code.co_name)
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
        log_to_elasticsearch('Get enabled transducers list', extra={'user': get_user(), 'virtue_id': request.args['virtueId']}, ret=ret, func_name=inspect.currentframe().f_code.co_name)
        return make_response(ret)

    except:

        print("Unexpected error:", sys.exc_info())

        return make_response(
            json.dumps(ErrorCodes.security['unspecifiedError']))


@bp.route('/security/transducer/enable_all_virtues', methods=['GET'])
@require_oauth()
def enable_all_virtues():

    ep = get_security_endpoint()

    if 'transducerId' not in request.args:
        return make_response(
            'ERROR: Required arguments: transducerId, configuration')

    try:
        if 'configuration' in request.args:
            ret = ep.transducer_all_virtues(request.args['transducerId'], request.args['configuration'], True)
        else:
            ret = ep.transducer_all_virtues(request.args['transducerId'], None, True)

        log_to_elasticsearch('Transducer enable all', extra={'transducer_id': request.args['transducerId']}, ret=ret, func_name=inspect.currentframe().f_code.co_name)
        return make_response(ret)

    except:
        print("Unexpected error:", sys.exc_info())
        return make_response(
            json.dumps(ErrorCodes.security['unspecifiedError']))


@bp.route('/security/transducer/disable_all_virtues', methods=['GET'])
@require_oauth()
def disable_all_virtues():
    ep = get_security_endpoint()

    if 'transducerId' not in request.args:
        return make_response(
            'ERROR: Required arguments: transducerId, configuration')

    try:
        if 'configuration' in request.args:
            ret = ep.transducer_all_virtues(request.args['transducerId'], request.args['configuration'], False)
        else:
            ret = ep.transducer_all_virtues(request.args['transducerId'], None, False)

        log_to_elasticsearch('Transducer enable all', extra={'transducer_id': request.args['transducerId']}, ret=ret,
                             func_name=inspect.currentframe().f_code.co_name)
        return make_response(ret)

    except:
        print("Unexpected error:", sys.exc_info())
        return make_response(
            json.dumps(ErrorCodes.security['unspecifiedError']))

@bp.route('/admin/valor/list', methods=['GET'])
@require_oauth()
def admin_valor_list():

    valors = []

    try:

        ep = get_admin_endpoint()
        valors = ep.valor_list()

    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(valors)


@bp.route('/admin/valor/create', methods=['GET'])
@require_oauth()
def admin_valor_create():

    valor_id = ''

    try:

        ep = get_admin_endpoint()
        valor_id = ep.valor_create()

    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(valor_id)


@bp.route('/admin/valor/create_pool', methods=['GET'])
@require_oauth()
def admin_valor_create_pool():

    valor_ids = []

    try:

        ep = get_admin_endpoint()
        valor_ids = ep.valor_create_pool(request.args['number_of_valors'])

    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(valor_ids)


@bp.route('/admin/valor/launch', methods=['GET'])
@require_oauth()
def admin_valor_launch():

    valor_id = ''

    try:

        ep = get_admin_endpoint()
        valor_id = ep.valor_launch(request.args['valor_id'])

    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(valor_id)


@bp.route('/admin/valor/stop', methods=['GET'])
@require_oauth()
def admin_valor_stop():

    valor_id = ''

    try:

        ep = get_admin_endpoint()
        valor_id = ep.valor_stop(request.args['valor_id'])

    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(valor_id)


@bp.route('/admin/valor/destroy', methods=['GET'])
@require_oauth()
def admin_valor_destroy():

    valor_id = ''

    try:

        ep = get_admin_endpoint()
        valor_id = ep.valor_destroy(request.args['valor_id'])

    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(valor_id)


@bp.route('/admin/valor/migrate_virtue', methods=['GET'])
@require_oauth()
def admin_valor_migrate_virtue():

    valor_id = ''

    try:

        ep = get_admin_endpoint()

        # destination_valor_id is an optional parm, set to None by default
        destination_valor_id = request.args.get('destination_valor_id', None)

        valor_id = ep.valor_migrate_virtue(
            request.args['virtue_id'],
            destination_valor_id)

    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(valor_id)


@bp.route('/admin/valor/auto_migration_start', methods=['GET'])
@require_oauth()
def admin_auto_migration_start():
    try:

        ep = get_admin_endpoint()

        migration_interval = request.args.get('migration_interval', None)

        if migration_interval:
            response = ep.auto_migration_start(migration_interval)
        else:
            response = ep.auto_migration_start()

        return make_response(response)

    except:
        print("Unexpected error:", sys.exc_info())

        return make_response(json.dumps(ErrorCodes.admin['unspecifiedError']))


@bp.route('/admin/valor/auto_migration_stop', methods=['GET'])
@require_oauth()
def admin_auto_migration_stop():

    try:

        ep = get_admin_endpoint()

        response = ep.auto_migration_stop()

        return make_response(response)

    except:
        print("Unexpected error:", sys.exc_info())

        return make_response(json.dumps(ErrorCodes.admin['unspecifiedError']))


@bp.route('/admin/valor/auto_migration_status', methods=['GET'])
@require_oauth()
def admin_auto_migration_status():

    try:

        ep = get_admin_endpoint()

        response = ep.auto_migration_status()

        return make_response(response)

    except:
        print("Unexpected error:", sys.exc_info())

        return make_response(json.dumps(ErrorCodes.admin['unspecifiedError']))


@bp.route('/admin/virtue/introspect_start', methods=['GET'])
@require_oauth()
def admin_virtue_introspect_start():
    
    virtue_id = ''

    try:
        ep = get_admin_endpoint()
        virtue_id = ep.virtue_introspect_start(
            request.args['virtueId'],
            request.args['interval'],
            request.args['modules'])
    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(virtue_id)

@bp.route('/admin/virtue/introspect_stop', methods=['GET'])
@require_oauth()
def admin_virtue_introspect_stop():
    virtue_id = ''

    try:
        ep = get_admin_endpoint()
        virtue_id = ep.virtue_introspect_stop(
            request.args['virtueId'])

    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(virtue_id)


@bp.route('/admin/virtue/introspect_start_all', methods=['GET'])
@require_oauth()
def admin_virtue_introspect_start_all():
    ret = ''

    try:
        ep = get_admin_endpoint()
        ret = ep.virtue_introspect_start_all(
            request.args['interval'],
            request.args['modules'])
    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(ret)


@bp.route('/admin/virtue/introspect_stop_all', methods=['GET'])
@require_oauth()
def admin_virtue_introspect_stop_all():
    ret = ''

    try:
        ep = get_admin_endpoint()
        ret = ep.virtue_introspect_stop_all()
    except:
        print("Unexpected error:", sys.exc_info())

    return make_response(ret)