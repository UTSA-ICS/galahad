from ldaplookup import LDAP
from services.errorcodes import ErrorCodes
from apiendpoint import EndPoint
from controller import CreateVirtueThread
from . import ldap_tools
import json
import random
import time

DEBUG_PERMISSIONS = False

class EndPoint_Admin():

    def __init__( self, user, password ):
        self.inst = LDAP( user, password )

        self.inst.bind_ldap()

    def application_list( self ):

        try:
            applications = self.inst.get_objs_of_type( 'OpenLDAPapplication' )
            if( applications == None ):
                return json.dumps( ErrorCodes.user['unspecifiedError'] )

            for application in applications:
                ldap_tools.parse_ldap( application )

            return json.dumps( applications )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    def resource_get( self, resourceId ):

        try:
            resource = self.inst.get_obj( 'cid', resourceId, objectClass='OpenLDAPresource', throw_error=True )
            if( resource == () ):
                return json.dumps( ErrorCodes.user['invalidId'] )
            ldap_tools.parse_ldap( resource )

            return json.dumps( resource )
        
        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    def resource_list( self ):

        try:
            resources = self.inst.get_objs_of_type( 'OpenLDAPresource' )
            if( resources == None ):
                return json.dumps( ErrorCodes.user['unspecifiedError'] )

            for resource in resources:
                ldap_tools.parse_ldap( resource )

            return json.dumps( resources )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    def resource_attach( self, resourceId, virtueId ):

        try:
            resource = self.inst.get_obj( 'cid', resourceId, objectClass='OpenLDAPresource', throw_error=True )
            if( resource == () ):
                return json.dumps( ErrorCodes.user['invalidResourceId'] )
            ldap_tools.parse_ldap( resource )

            virtue = self.inst.get_obj( 'cid', virtueId, objectClass='OpenLDAPvirtue', throw_error=True )
            if( virtue == () ):
                return json.dumps( ErrorCodes.user['invalidVirtueId'] )
            ldap_tools.parse_ldap( virtue )

            if( virtue['state'] == 'DELETING' ):
                return json.dumps( ErrorCodes.user['invalidVirtueState'] )

            if( resourceId in virtue['resourceIds'] ):
                return json.dumps( ErrorCodes.user['cantAttach'] )

            return json.dumps( ErrorCodes.user['notImplemented'] )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    def resource_detach( self, resourceId, virtueId ):

        try:
            resource = self.inst.get_obj( 'cid', resourceId, objectClass='OpenLDAPresource', throw_error=True )
            if( resource == () ):
                return json.dumps( ErrorCodes.user['invalidResourceId'] )
            ldap_tools.parse_ldap( resource )

            virtue = self.inst.get_obj( 'cid', virtueId, objectClass='OpenLDAPvirtue', throw_error=True )
            if( virtue == () ):
                return json.dumps( ErrorCodes.user['invalidVirtueId'] )
            ldap_tools.parse_ldap( virtue )

            if( resourceId not in virtue['resourceIds'] ):
                return json.dumps( ErrorCodes.user['cantDetach'] )

            return json.dumps( ErrorCodes.user['notImplemented'] )
        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    def role_create( self, role ):

        try:
            if(  'name' not in role or
                 type( role['name'] ) != str or
                 'version' not in role or
                 type( role['version'] ) != str or
                 'applicationIds' not in role or
                 type( role['applicationIds'] ) != list or
                 'startingResourceIds' not in role or
                 type( role['startingResourceIds'] ) != list or
                 'startingTransducerIds' not in role or
                 type( role['startingTransducerIds'] ) != list ):
                return json.dumps( ErrorCodes.user['invalidFormat'] )

            for a in role['applicationIds']:
                app_test = self.inst.get_obj( 'cid', a, objectClass='OpenLDAPapplication', throw_error=True )
                if( app_test == () ):
                    return json.dumps( ErrorCodes.user['invalidApplicationId'] )

            for r in role['startingResourceIds']:
                res_test = self.inst.get_obj( 'cid', r, objectClass='OpenLDAPresource', throw_error=True )
                if( res_test == () ):
                    return json.dumps( ErrorCodes.user['invalidResourceId'] )

            for t in role['startingTransducerIds']:
                tr_test = self.inst.get_obj( 'cid', t, objectClass='OpenLDAPtransducer', throw_error=True )
                if( tr_test == () ):
                    return json.dumps( ErrorCodes.user['invalidTransducerId'] )

            role['id'] = '{0}{1}'.format( role['name'], int(time.time()) )

            # Todo: Create AWS AMI file with BBN's assembler
            #role['ami'] = AWS.aws_image_id

            ldap_role = ldap_tools.to_ldap( role, 'OpenLDAProle' )

            ret = self.inst.add_obj( ldap_role, 'roles', 'cid' )

            if( ret != 0 ):
                return json.dumps( ErrorCodes.user['storageError'] )

            # Call a controller thread to create a new standby virtue on a new thread
            thr = CreateVirtueThread( self.inst.email, self.inst.password, role['id'], role=role )
            thr.start()
            
            return json.dumps( role )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    def role_list( self ):

        try:
            roles = self.inst.get_objs_of_type( 'OpenLDAProle' )
            if( roles == None ):
                return json.dumps( ErrorCodes.user['unspecifiedError'] )

            for role in roles:
                ldap_tools.parse_ldap( role )

            return json.dumps( roles )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    def system_export( self ):
        return json.dumps( ErrorCodes.user['notImplemented'] )

    def system_import( self, data ):
        return json.dumps( ErrorCodes.user['notImplemented'] )

    def test_import_user( self, which ):
        return json.dumps( ErrorCodes.user['notImplemented'] )

    def test_import_application( self, which ):
        return json.dumps( ErrorCodes.user['notImplemented'] )

    def test_import_role( self, which ):
        return json.dumps( ErrorCodes.user['notImplemented'] )

    def user_list( self ):

        try:
            users = self.inst.get_objs_of_type( 'OpenLDAPuser' )
            if( users == None ):
                return json.dumps( ErrorCodes.user['unspecifiedError'] )

            for user in users:
                ldap_tools.parse_ldap( user )

            return json.dumps( users )
        
        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    def user_get( self, username ):

        try:
            user = self.inst.get_obj( 'cusername', username, objectClass='OpenLDAPuser', throw_error=True )
            if( user == () ):
                return json.dumps( ErrorCodes.user['invalidUsername'] )
            ldap_tools.parse_ldap( user )

            return json.dumps( user )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    def user_virtue_list( self, username ):

        user = self.inst.get_obj( 'cusername', username, objectClass='OpenLDAPuser' )
        if( user == () ):
            return json.dumps( ErrorCodes.user['invalidUsername'] )
        elif( user == None ):
            return json.dumps( ErrorCodes.user['unspecifiedError'] )
        
        ep = EndPoint( self.inst.email, self.inst.password )

        return ep.user_role_list( username )

    def user_role_authorize( self, username, roleId ):

        try:
            user = self.inst.get_obj( 'cusername', username, objectClass='OpenLDAPuser', throw_error=True )
            if( user == () ):
                return json.dumps( ErrorCodes.user['invalidUsername'] )
            ldap_tools.parse_ldap( user )

            role = self.inst.get_obj( 'cid', roleId, objectClass='OpenLDAProle', throw_error=True )
            if( role == () ):
                if( roleId in user['authorizedRoleIds'] ):
                    # The user is authorized for a nonexistant role...
                    # Remove it from their list?
                    1+1
                return json.dumps( ErrorCodes.user['invalidRoleId'] )
            ldap_tools.parse_ldap( role )

            if( roleId in user['authorizedRoleIds'] ):
                return json.dumps( ErrorCodes.user['userAlreadyAuthorized'] )

            user['authorizedRoleIds'].append( roleId )

            ldap_user = ldap_tools.to_ldap( user, 'OpenLDAPuser' )

            self.inst.modify_obj( 'cusername', username, ldap_user, objectClass='OpenLDAPuser', throw_error=True )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )

    def user_role_unauthorize( self, username, roleId ):
        
        try:
            user = self.inst.get_obj( 'cusername', username, objectClass='OpenLDAPuser', throw_error=True )
            if( user == () ):
                return json.dumps( ErrorCodes.user['invalidUsername'] )
            ldap_tools.parse_ldap( user )

            role = self.inst.get_obj( 'cid', roleId, objectClass='OpenLDAProle', throw_error=True )
            if( roleId not in user['authorizedRoleIds'] and role == () ):
                # If the role does not exist AND the user isn't 'authorized' for it,
                #  return error.
                # If the user is authorized for a nonexistant role, the admin
                #  may be trying to clean up an error
                return json.dumps( ErrorCodes.user['invalidRoleId'] )
            elif( roleId not in user['authorizedRoleIds'] ):
                return json.dumps( ErrorCodes.user['userNotAuthorized'][12] )
            ldap_tools.parse_ldap( role )

            virtues = self.inst.get_objs_of_type( 'OpenLDAPvirtue' )
            for v in virtues:
                ldap_tools.parse_ldap(v)

                if( v['username'] == username and v['roleId'] == roleId ):
                    # Todo: Check if the user is logged on
                    return json.dumps( ErrorCodes.user['userUsingVirtue'] )

            for r in user['authorizedRoleIds']:
                if( r == roleId ):
                    del r

            ldap_user = ldap_tools.to_ldap( user, 'OpenLDAPuser' )

            self.inst.modify_obj( 'cusername', username, ldap_user, objectClass='OpenLDAPuser', throw_error=True )

        except Exception as e:
            print( "Error: {0}".format(e) )
            return json.dumps( ErrorCodes.user['unspecifiedError'] )
