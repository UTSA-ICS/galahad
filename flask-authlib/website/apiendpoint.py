from ldaplookup import LDAP
from services.errorcodes import ErrorCodes
import json
import ldap.modlist

DEBUG_PERMISSIONS = False

class EndPoint():

    def __init__( self, user, password ):
        self.inst = LDAP( user, password )

        self.inst.bind_ldap()

    @staticmethod
    def parse_ldap( data ):

        parse_map = {'cappIds': 'applicationIds',
                     'cstartResIds': 'startingResourceIds',
                     'cstartTransIds': 'startingTransducerIds',
                     'cstartConfig': 'startingConfiguration',
                     'creqAccess': 'requiredAccess',
                     'cauthRoleIds': 'authorizedRoleIds',
                     'cresIds': 'resourceIds',
                     'ctransIds': 'transducerIds'}

        entries_with_lists = ['applicationIds',
                              'startingResourceIds',
                              'startingTransducerIds',
                              'requiredAccess',
                              'authorizedRoleIds',
                              'resourceIds',
                              'transducerIds']

        if( 'ou' in data.keys() ):
            del data['ou']
        if( 'objectClass' in data.keys() ):
            del data['objectClass']
        
        for k in data.keys():
            if( k in parse_map.keys() ):
                data[ parse_map[k] ] = data.pop(k)
            elif( k[0] == 'c' and k != 'credentials' ):
                data[ k[ 1:len(k) ] ] = data.pop(k)

        for k in data.keys():
            if( k not in entries_with_lists
                and type( data[k] ) == list ):
                data[k] = data[k][0]
            elif( k in entries_with_lists
                  and type( data[k] ) == list
                  and data[k][0] == '[]' ):
                data[k] = []

    @staticmethod
    def to_ldap( data, objectClass ):

        if( type(data) != dict ):
            return None

        parse_map = {'id': 'cid',
                     'version': 'cversion',
                     'os': 'cos',
                     'type': 'ctype',
                     'unc': 'cunc',
                     'credentials': 'ccredentials',
                     'applicationIds': 'cappIds',
                     'startingResourceIds': 'cstartResIds',
                     'startingTransducerIds': 'cstartTransIds',
                     'startEnabled': 'cstartEnabled',
                     'startingConfiguration': 'cstartConfig',
                     'requiredAccess': 'creqAccess',
                     'username': 'cusername',
                     'authorizedRoleIds': 'cauthRoleIds',
                     'token': 'ctoken',
                     'expiration': 'cexpiration',
                     'roleId': 'croleId',
                     'resourceIds': 'cresIds',
                     'transducerIds': 'ctransIds',
                     'state': 'cstate',
                     'ipAddress': 'cipAddress' }

        modified_data = { 'objectClass': objectClass,
                          'ou': 'Virtue' }

        for k in data.keys():
            if( k in parse_map.keys() ):
                modified_data[ parse_map[k] ] = data[k]
            else:
                modified_data[k] = data[k]

        for k in modified_data.keys():
            if( modified_data[k] == [] ):
                modified_data[k] = '[]'

        return modified_data

    # Retrieve information about the specified application
    def application_get( self, username, applicationId ):

        try:
            if( not DEBUG_PERMISSIONS ):

                user = self.inst.get_obj( 'cusername', username, 'openLDAPuser' )
                if( user == None or user == () ):
                    # User was already validated, but can't be accessed now...
                    return json.dumps( ErrorCodes.user['unspecifiedError'] )
                self.parse_ldap( user )

            app = self.inst.get_obj( 'cid', applicationId, 'openLDAPapplication', True )
            if( app == () ):
                return json.dumps( ErrorCodes.user['invalidId'] )
            self.parse_ldap( app )

            if( DEBUG_PERMISSIONS ):
                return json.dumps(app)

            for roleId in user['authorizedRoleIds']:
                role = self.inst.get_obj( 'cid', roleId, 'openLDAProle' )
                if( role == None or role == () ):
                    # Error!
                    continue
                self.parse_ldap( role )

                if( applicationId in role['applicationIds'] ):
                    # User is authorized to access this application.
                    return json.dumps(app)

            return json.dumps( ErrorCodes.user['userNotAuthorized'] )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    # Retrieve data about the specified role
    def role_get( self, username, roleId ):

        try:
            if( not DEBUG_PERMISSIONS ):
                user = self.inst.get_obj( 'cusername', username, 'openLDAPuser' )
                if( user == None or user == () ):
                    return json.dumps( ErrorCodes.user['unspecifiedError'] )
                self.parse_ldap( user )

            role = self.inst.get_obj( 'cid', roleId, 'openLDAProle', True )
            if( role == () ):
                return json.dumps( ErrorCodes.user['invalidId'] )
            self.parse_ldap( role )

            if( DEBUG_PERMISSIONS or roleId in user['authorizedRoleIds'] ):
                return json.dumps(role)

            return json.dumps( ErrorCodes.user['userNotAuthorized'] )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    # Retrieve a list of roles available to user
    def user_role_list( self, username ):
        
        try:
            user = self.inst.get_obj( 'cusername', username, 'openLDAPuser' )
            if( user == None or user == () ):
                return json.dumps( ErrorCodes.user['unspecifiedError'] )
            self.parse_ldap( user )

            roles = []
        
            for roleId in user['authorizedRoleIds']:
                role = self.inst.get_obj( 'cid', roleId, 'openLDAProle' )
                if( role == None or role == () ):
                    continue
                self.parse_ldap( role )

                roles.append( role )

            return json.dumps(roles)

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    # Retrieve a list of virtues available to user
    def user_virtue_list( self, username ):

        try:
            virtues_raw = self.inst.get_objs_of_type( 'OpenLDAPvirtue' )
            if( virtues_raw == None ):
                return json.dumps( ErrorCodes.user['unspecifiedError'] )

            virtues_ret = []
        
            for virtue in virtues_raw:
                self.parse_ldap( virtue[1] )

                if( virtue[1]['username'] == username ):
                    virtues_ret.append( virtue[1] )

            return json.dumps(virtues_ret)

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    # Retrieve information about the specified virtue
    def virtue_get( self, username, virtueId ):
        
        try:
            virtue = self.inst.get_obj( 'cid', virtueId, 'OpenLDAPvirtue', True )
            if( virtue == () ):
                return json.dumps( ErrorCodes.user['invalidId'] )
            self.parse_ldap( virtue )

            if( virtue['username'] == username or DEBUG_PERMISSIONS ):
                return json.dumps( virtue )

            return json.dumps( ErrorCodes.user['userNotAuthorized'] )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    # Create a virtue for the specified role, but do not launch it yet
    def virtue_create( self, username, roleId ):

        try:
            user = None
            role = None
            resources = []
            transducers = []
            virtue_dict = {}

            user = self.inst.get_obj( 'cusername', username, 'OpenLDAPuser' )
            if( user == None or user == () ):
                return json.dumps( ErrorCodes.user['unspecifiedError'] )
            self.parse_ldap( user )

            role = self.inst.get_obj( 'cid', roleId, 'OpenLDAProle', True )
            if( role == () ):
                return json.dumps( ErrorCodes.user['invalidRoleId'] )
            self.parse_ldap( role )

            if( roleId not in user['authorizedRoleIds'] ):
                return json.dumps( ErrorCodes.user['userNotAuthorizedForRole'] )

            virtue = None
            curr_virtues = self.inst.get_objs_of_type( 'OpenLDAPvirtue' )
            for v in curr_virtues:
                self.parse_ldap( v[1] )
                if( v[1]['username'] == 'NULL' and v[1]['roleId'] == roleId ):
                    virtue = v[1]
                elif( v[1]['username'] == username and v[1]['roleId'] == roleId ):
                    return json.dumps( ErrorCodes.user['virtueAlreadyExistsForRole'] )

            for rid in role['startingResourceIds']:

                resource = self.inst.get_obj( 'cid', rid, 'OpenLDAPresource', True )
                if( resource == () ):
                    continue
                self.parse_ldap( resource )

                resources.append( resource )

            for tid in role['startingTransducerIds']:

                transducer = self.inst.get_obj( 'cid', tid, 'OpenLDAPtransducer', True )
                if( transducer == () ):
                    continue
                self.parse_ldap( transducer )

                transducers.append( transducer )

            if( virtue == None ):
                # Pending virtue does not exist
                return json.dumps( ErrorCodes.user['resourceCreationError'] )

            virtue['username'] = username

            virtue_ldap = self.to_ldap( virtue, 'OpenLDAPvirtue' )

            ret = self.inst.modify_obj( 'cid', virtue_ldap['cid'], virtue_ldap, objectClass='OpenLDAPvirtue', throw_error=True )

            if( ret != 0 ):
                return json.dumps( ErrorCodes.user['resourceCreationError'] )

            # Return the whole thing
            # return json.dumps( virtue )

            # Return a json of the id and ip address
            return json.dumps( {'ipAddress': virtue['ipAddress'], 'id': virtue['id']} )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    # Launch the specified virtue, which must have already been created
    def virtue_launch( self, username, virtueId ):

        try:
            virtue = self.inst.get_obj( 'cid', virtueId, 'OpenLDAPvirtue', True )
            if( virtue == () ):
                return json.dumps( ErrorCodes.user['invalidId'] )
            self.parse_ldap( virtue )

            if( virtue['username'] != username ):
                return json.dumps( ErrorCodes.user['userNotAuthorized'] )

            if( virtue['state'] == 'RUNNING' or virtue['state'] == 'LAUNCHING' ):
                return json.dumps( ErrorCodes.user['virtueAlreadyLaunched'] )
            elif( virtue['state'] != 'STOPPED' ):
                return json.dumps( ErrorCodes.user['virtueStateCannotBeLaunched'] )

            # Todo: Launch it

            return json.dumps( ErrorCodes.user['notImplemented'] )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    # Stop the specified virtue, but do not destroy it
    def virtue_stop( self, username, virtueId ):

        try:
            virtue = self.inst.get_obj( 'cid', virtueId, 'OpenLDAPvirtue', True )
            if( virtue == () ):
                return json.dumps( ErrorCodes.user['invalidId'] )
            self.parse_ldap( virtue )

            if( virtue['username'] != username ):
                return json.dumps( ErrorCodes.user['userNotAuthorized'] )

            if( virtue['state'] == 'STOPPED' ):
                return json.dumps( ErrorCodes.user['virtueAlreadyStopped'] )
            elif( virtue['state'] != 'RUNNING' ):
                return json.dumps( ErrorCodes.user['virtueStateCannotBeStopped'] )

            # Todo: Stop it
        
            return json.dumps( ErrorCodes.user['notImplemented'] )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    # Destroy the specified stopped virtue
    def virtue_destroy( self, username, virtueId ):

        try:
            virtue = self.inst.get_obj( 'cid', virtueId, 'OpenLDAPvirtue', True )
            if( virtue == () ):
                return json.dumps( ErrorCodes.user['invalidId'] )
            self.parse_ldap( virtue )

            if( virtue['username'] != username ):
                return json.dumps( ErrorCodes.user['userNotAuthorized'] )

            if( virtue['state'] != 'STOPPED' ):
                return json.dumps( ErrorCodes.user['virtueNotStopped'] )

            # Todo: Destroy it
        
            return json.dumps( ErrorCodes.user['notImplemented'] )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    # Launch an application on the specified virtue
    def virtue_application_launch( self, username, virtueId, applicationId ):

        try:
            virtue = self.inst.get_obj( 'cid', virtueId, 'OpenLDAPvirtue', True )
            if( virtue == () ):
                return json.dumps( ErrorCodes.user['invalidVirtueId'] )
            self.parse_ldap( virtue )

            if( virtue['username'] != username ):
                return json.dumps( ErrorCodes.user['userNotAuthorized'] )

            if( virtue['state'] != 'RUNNING' ):
                return json.dumps( ErrorCodes.user['virtueNotRunning'] )

            app = self.inst.get_obj( 'cid', applicationId, 'OpenLDAPapplication', True )
            if( app == () ):
                return json.dumps( ErrorCodes.user['invalidApplicationId'] )
            self.parse_ldap( app )

            role = self.inst.get_obj( 'cid', virtue['roleId'], 'OpenLDAProle' )
            if( role == None or role == () ):
                return json.dumps( ErrorCodes.user['unspecifiedError'] )
            self.parse_ldap( role )

            if( app['id'] not in role['applicationIds'] ):
                return json.dumps( ErrorCodes.user['applicationNotInVirtue'] )

            if( app['id'] in virtue['applicationIds'] ):
                return json.dumps( ErrorCodes.user['applicationAlreadyLaunched'] )

            # Todo: Launch app through ssh to virtue's ip address
        
            return json.dumps( ErrorCodes.user['notImplemented'] )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    # Stop an application on the specified virtue
    def virtue_application_stop( self, username, virtueId, applicationId ):

        try:
            virtue = self.inst.get_obj( 'cid', virtueId, 'OpenLDAPvirtue', True )
            if( virtue == () ):
                return json.dumps( ErrorCodes.user['invalidVirtueId'] )
            self.parse_ldap( virtue )

            if( virtue['username'] != username ):
                return json.dumps( ErrorCodes.user['userNotAuthorized'] )

            if( virtue['state'] != 'RUNNING' ):
                return json.dumps( ErrorCodes.user['virtueNotRunning'] )

            app = self.inst.get_obj( 'cid', applicationId, 'OpenLDAPapplication', True )
            if( app == () ):
                return json.dumps( ErrorCodes.user['invalidApplicationId'] )
            self.parse_ldap( app )

            role = self.inst.get_obj( 'cid', virtue['roleId'], 'OpenLDAProle' )
            if( role == None or role == () ):
                return json.dumps( ErrorCodes.user['unspecifiedError'] )
            self.parse_ldap( role )

            if( app['id'] not in role['applicationIds'] ):
                return json.dumps( ErrorCodes.user['applicationNotInVirtue'] )

            if( app['id'] not in virtue['applicationIds'] ):
                return json.dumps( ErrorCodes.user['applicationAlreadyStopped'] )

            # Todo: Stop app through ssh to virtue's ip address
        
            return json.dumps( ErrorCodes.user['notImplemented'] )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )


if( __name__ == '__main__' ):

    ep = EndPoint('jmitchell@virtue.com', 'Test123!' )
    
    print ( ep.inst.query_ldap( 'cn', 'jmitchell' ) )

    fake_token = {'username': 'jmitchell',
                  'token': 3735928559,
                  'expiration': 0}
    
    print( ep.application_get( fake_token, 'firefox1' ) )
    print( ep.role_get( fake_token, 'Test' ) )
    print( ep.user_role_list( fake_token ) )
    print( ep.user_virtue_list( fake_token ) )
    print( ep.virtue_get( fake_token, 'TestVirtue' ) )
