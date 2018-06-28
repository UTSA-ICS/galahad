import json

from ldaplookup import LDAP
from services.errorcodes import ErrorCodes
from . import ldap_tools
from aws import AWS

DEBUG_PERMISSIONS = False


class EndPoint():
    def __init__(self, user, password):
        self.inst = LDAP(user, password)

        self.inst.bind_ldap()

    # Retrieve information about the specified application
    def application_get(self, username, applicationId):

        try:
            if (not DEBUG_PERMISSIONS):

                user = self.inst.get_obj('cusername', username, 'openLDAPuser')
                if (user == None or user == ()):
                    # User was already validated, but can't be accessed now...
                    return json.dumps(ErrorCodes.user['unspecifiedError'])
                ldap_tools.parse_ldap(user)

            app = self.inst.get_obj('cid', applicationId,
                                    'openLDAPapplication', True)
            if (app == ()):
                return json.dumps(ErrorCodes.user['invalidId'])
            ldap_tools.parse_ldap(app)

            if (DEBUG_PERMISSIONS):
                return json.dumps(app)

            for roleId in user['authorizedRoleIds']:
                role = self.inst.get_obj('cid', roleId, 'openLDAProle')
                if (role == None or role == ()):
                    # Error!
                    continue
                ldap_tools.parse_ldap(role)

                if (applicationId in role['applicationIds']):
                    # User is authorized to access this application.
                    return json.dumps(app)

            return json.dumps(ErrorCodes.user['userNotAuthorized'])

        except Exception as e:
            print("Error: {0}".format(e))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Retrieve data about the specified role
    def role_get(self, username, roleId):

        try:
            if (not DEBUG_PERMISSIONS):
                user = self.inst.get_obj('cusername', username, 'openLDAPuser')
                if (user == None or user == ()):
                    return json.dumps(ErrorCodes.user['unspecifiedError'])
                ldap_tools.parse_ldap(user)

            role = self.inst.get_obj('cid', roleId, 'openLDAProle', True)
            if (role == ()):
                return json.dumps(ErrorCodes.user['invalidId'])
            ldap_tools.parse_ldap(role)

            if (DEBUG_PERMISSIONS or roleId in user['authorizedRoleIds']):

                # Now get the IP address of the virtue associated with this user/role
                virtue_ip = 'NULL'

                ldap_virtues = self.inst.get_objs_of_type('OpenLDAPvirtue')
                virtues = ldap_tools.parse_ldap_list(ldap_virtues)

                for v in virtues:
                    if (v['username'] == username and v['roleId'] == roleId):
                        aws = AWS()
                        virtue = aws.populate_virtue_dict(v)
                        virtue_ip = virtue['ipAddress']
                        break

                role['ipAddress'] = virtue_ip
                del role['amiId']

                return json.dumps(role)

            return json.dumps(ErrorCodes.user['userNotAuthorized'])

        except Exception as e:
            print("Error: {0}".format(e))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Retrieve a list of roles available to user
    def user_role_list(self, username):

        try:
            user = self.inst.get_obj('cusername', username, 'openLDAPuser')
            if (user == None or user == ()):
                return json.dumps(ErrorCodes.user['unspecifiedError'])
            ldap_tools.parse_ldap(user)

            roles = []

            ldap_virtues = self.inst.get_objs_of_type('OpenLDAPvirtue')
            virtues = ldap_tools.parse_ldap_list(ldap_virtues)

            aws = AWS()
            for roleId in user['authorizedRoleIds']:
                role = self.inst.get_obj('cid', roleId, 'openLDAProle')
                if (role == None or role == ()):
                    continue
                ldap_tools.parse_ldap(role)

                # Now get the IP address of the virtue associated with this user/role
                virtue_ip = 'NULL'

                for v in virtues:
                    if (v['username'] == username and v['roleId'] == roleId):
                        virtue = aws.populate_virtue_dict(v)
                        virtue_ip = virtue['ipAddress']
                        break

                role['ipAddress'] = virtue_ip
                del role['amiId']

                roles.append(role)

            return json.dumps(roles)

        except Exception as e:
            print("Error: {0}".format(e))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Retrieve a list of virtues available to user
    def user_virtue_list(self, username):

        try:
            virtues_raw = self.inst.get_objs_of_type('OpenLDAPvirtue')
            if (virtues_raw == None):
                return json.dumps(ErrorCodes.user['unspecifiedError'])

            virtues_ret = []

            aws = AWS()
            for virtue in virtues_raw:
                ldap_tools.parse_ldap(virtue[1])

                if (virtue[1]['username'] == username):
                    v = aws.populate_virtue_dict(virtue[1])
                    del v['awsInstanceId']
                    virtues_ret.append(v)

            return json.dumps(virtues_ret)

        except Exception as e:
            print("Error: {0}".format(e))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Retrieve information about the specified virtue
    def virtue_get(self, username, virtueId):

        try:
            virtue = self.inst.get_obj('cid', virtueId, 'OpenLDAPvirtue', True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.user['invalidId'])
            ldap_tools.parse_ldap(virtue)

            if (virtue['username'] == username or DEBUG_PERMISSIONS):
                aws = AWS()
                virtue = aws.populate_virtue_dict(virtue)
                del virtue['awsInstanceId']
                return json.dumps(virtue)

            return json.dumps(ErrorCodes.user['userNotAuthorized'])

        except Exception as e:
            print("Error: {0}".format(e))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Create a virtue for the specified role, but do not launch it yet
    def virtue_create(self, username, roleId, use_aws=True):

        try:
            user = None
            role = None
            resources = []
            transducers = []
            virtue_dict = {}

            user = self.inst.get_obj('cusername', username, 'OpenLDAPuser')
            if (user == None or user == ()):
                return json.dumps(ErrorCodes.user['unspecifiedError'])
            ldap_tools.parse_ldap(user)

            role = self.inst.get_obj('cid', roleId, 'OpenLDAProle', True)
            if (role == ()):
                return json.dumps(ErrorCodes.user['invalidRoleId'])
            ldap_tools.parse_ldap(role)

            if (roleId not in user['authorizedRoleIds']):
                return json.dumps(ErrorCodes.user['userNotAuthorizedForRole'])

            virtue = None
            curr_virtues = self.inst.get_objs_of_type('OpenLDAPvirtue')
            for v in curr_virtues:
                ldap_tools.parse_ldap(v[1])
                if (v[1]['username'] == 'NULL' and v[1]['roleId'] == roleId):
                    virtue = v[1]
                elif (v[1]['username'] == username
                      and v[1]['roleId'] == roleId):
                    return json.dumps(
                        ErrorCodes.user['virtueAlreadyExistsForRole'])

            for rid in role['startingResourceIds']:

                resource = self.inst.get_obj('cid', rid, 'OpenLDAPresource',
                                             True)
                if (resource == ()):
                    continue
                ldap_tools.parse_ldap(resource)

                resources.append(resource)

            for tid in role['startingTransducerIds']:

                transducer = self.inst.get_obj('cid', tid,
                                               'OpenLDAPtransducer', True)
                if (transducer == ()):
                    continue
                ldap_tools.parse_ldap(transducer)

                transducers.append(transducer)

            if (virtue == None):
                # Pending virtue does not exist
                return json.dumps(ErrorCodes.user['resourceCreationError'])

            virtue['username'] = username

            virtue_ldap = ldap_tools.to_ldap(virtue, 'OpenLDAPvirtue')

            ret = self.inst.modify_obj(
                'cid',
                virtue_ldap['cid'],
                virtue_ldap,
                objectClass='OpenLDAPvirtue',
                throw_error=True)

            if (ret != 0):
                return json.dumps(ErrorCodes.user['resourceCreationError'])

            # Return the whole thing
            # return json.dumps( virtue )

            # Return a json of the id and ip address
            aws = AWS()
            virtue = aws.populate_virtue_dict(virtue)
            return json.dumps({
                'ipAddress': virtue['ipAddress'],
                'id': virtue['id']
            })

        except Exception as e:
            print("Error: {0}".format(e))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Launch the specified virtue, which must have already been created
    def virtue_launch(self, username, virtueId, use_aws=True):

        try:
            virtue = self.inst.get_obj('cid', virtueId, 'OpenLDAPvirtue', True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.user['invalidId'])
            ldap_tools.parse_ldap(virtue)

            aws = AWS()
            virtue = aws.populate_virtue_dict(virtue)

            if (virtue['username'] != username):
                return json.dumps(ErrorCodes.user['userNotAuthorized'])

            if (virtue['state'] == 'RUNNING'
                    or virtue['state'] == 'LAUNCHING'):
                return json.dumps(ErrorCodes.user['virtueAlreadyLaunched'])
            elif (virtue['state'] != 'STOPPED'):
                return json.dumps(
                    ErrorCodes.user['virtueStateCannotBeLaunched'])

            # Todo: Launch it

            return json.dumps(ErrorCodes.user['notImplemented'])

        except Exception as e:
            print("Error: {0}".format(e))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Stop the specified virtue, but do not destroy it
    def virtue_stop(self, username, virtueId, use_aws=True):

        try:
            virtue = self.inst.get_obj('cid', virtueId, 'OpenLDAPvirtue', True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.user['invalidId'])
            ldap_tools.parse_ldap(virtue)

            aws = AWS()
            virtue = aws.populate_virtue_dict(virtue)

            if (virtue['username'] != username):
                return json.dumps(ErrorCodes.user['userNotAuthorized'])

            if (virtue['state'] == 'STOPPED'):
                return json.dumps(ErrorCodes.user['virtueAlreadyStopped'])
            elif (virtue['state'] != 'RUNNING'):
                return json.dumps(
                    ErrorCodes.user['virtueStateCannotBeStopped'])

            # Todo: Stop it

            return json.dumps(ErrorCodes.user['notImplemented'])

        except Exception as e:
            print("Error: {0}".format(e))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Destroy the specified stopped virtue
    def virtue_destroy(self, username, virtueId, use_aws=True):

        try:
            virtue = self.inst.get_obj('cid', virtueId, 'OpenLDAPvirtue', True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.user['invalidId'])
            ldap_tools.parse_ldap(virtue)

            aws = AWS()
            virtue = aws.populate_virtue_dict(virtue)

            if (virtue['username'] != username):
                return json.dumps(ErrorCodes.user['userNotAuthorized'])

            if (use_aws == False):
                self.inst.del_obj('cid', virtue['id'], throw_error=True)
                return

            if (virtue['state'] != 'STOPPED'):
                return json.dumps(ErrorCodes.user['virtueNotStopped'])

            aws_res = aws.instance_destroy(virtue['awsInstanceId'], block=False)

            aws_state = aws_res.state['Name']

            if (aws_state == 'shutting-down'):
                return  # Success!

            elif (aws_state == 'terminated'):
                self.inst.del_obj('cid', virtue['id'], throw_error=True)
                return  # Success!

            else:
                return json.dumps(ErrorCodes.user['serverDestroyError'])

        except Exception as e:
            print("Error: {0}".format(e))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Launch an application on the specified virtue
    def virtue_application_launch(self, username, virtueId, applicationId):

        try:
            virtue = self.inst.get_obj('cid', virtueId, 'OpenLDAPvirtue', True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.user['invalidVirtueId'])
            ldap_tools.parse_ldap(virtue)

            aws = AWS()
            virtue = aws.populate_virtue_dict(virtue)

            if (virtue['username'] != username):
                return json.dumps(ErrorCodes.user['userNotAuthorized'])

            if (virtue['state'] != 'RUNNING'):
                return json.dumps(ErrorCodes.user['virtueNotRunning'])

            app = self.inst.get_obj('cid', applicationId,
                                    'OpenLDAPapplication', True)
            if (app == ()):
                return json.dumps(ErrorCodes.user['invalidApplicationId'])
            ldap_tools.parse_ldap(app)

            role = self.inst.get_obj('cid', virtue['roleId'], 'OpenLDAProle')
            if (role == None or role == ()):
                return json.dumps(ErrorCodes.user['unspecifiedError'])
            ldap_tools.parse_ldap(role)

            if (app['id'] not in role['applicationIds']):
                return json.dumps(ErrorCodes.user['applicationNotInVirtue'])

            if (app['id'] in virtue['applicationIds']):
                return json.dumps(
                    ErrorCodes.user['applicationAlreadyLaunched'])

            # Todo: Launch app through ssh to virtue's ip address

            return json.dumps(ErrorCodes.user['notImplemented'])

        except Exception as e:
            print("Error: {0}".format(e))
            return json.dumps(ErrorCodes.user['unspecifiedError'])

    # Stop an application on the specified virtue
    def virtue_application_stop(self, username, virtueId, applicationId):

        try:
            virtue = self.inst.get_obj('cid', virtueId, 'OpenLDAPvirtue', True)
            if (virtue == ()):
                return json.dumps(ErrorCodes.user['invalidVirtueId'])
            ldap_tools.parse_ldap(virtue)

            aws = AWS()
            virtue = aws.populate_virtue_dict(virtue)

            if (virtue['username'] != username):
                return json.dumps(ErrorCodes.user['userNotAuthorized'])

            if (virtue['state'] != 'RUNNING'):
                return json.dumps(ErrorCodes.user['virtueNotRunning'])

            app = self.inst.get_obj('cid', applicationId,
                                    'OpenLDAPapplication', True)
            if (app == ()):
                return json.dumps(ErrorCodes.user['invalidApplicationId'])
            ldap_tools.parse_ldap(app)

            role = self.inst.get_obj('cid', virtue['roleId'], 'OpenLDAProle')
            if (role == None or role == ()):
                return json.dumps(ErrorCodes.user['unspecifiedError'])
            ldap_tools.parse_ldap(role)

            if (app['id'] not in role['applicationIds']):
                return json.dumps(ErrorCodes.user['applicationNotInVirtue'])

            if (app['id'] not in virtue['applicationIds']):
                return json.dumps(ErrorCodes.user['applicationAlreadyStopped'])

            # Todo: Stop app through ssh to virtue's ip address

            return json.dumps(ErrorCodes.user['notImplemented'])

        except Exception as e:
            print("Error: {0}".format(e))
            return json.dumps(ErrorCodes.user['unspecifiedError'])


if (__name__ == '__main__'):

    ep = EndPoint('jmitchell@virtue.com', 'Test123!')

    print(ep.inst.query_ldap('cn', 'jmitchell'))

    fake_token = {
        'username': 'jmitchell',
        'token': 3735928559,
        'expiration': 0
    }

    print(ep.application_get(fake_token, 'firefox1'))
    print(ep.role_get(fake_token, 'Test'))
    print(ep.user_role_list(fake_token))
    print(ep.user_virtue_list(fake_token))
    print(ep.virtue_get(fake_token, 'TestVirtue'))
