import ldap
import ldap.modlist

LDAP_DATABASE_URI = "ldap://localhost"
AD_DATABASE_URI = "ldap://ad.galahad.com"

LDAP_PROTOCOL_VERSION = 3
LDAP_QUERY_DN = "dc=canvas,dc=virtue,dc=com"
LDAP_VIRTUE_DN = "ou=virtue,dc=canvas,dc=virtue,dc=com"
AD_QUERY_DN = "ou=virtue,dc=virtue,dc=com"


class LDAP():

    email = None
    password = None
    conn = None

    def __init__(self, email, password):
        self.email = email
        self.password = password

    def get_ldap_connection(self):
        self.conn = ldap.initialize(LDAP_DATABASE_URI)
        self.conn.protocol_version = LDAP_PROTOCOL_VERSION

    def get_ad_connection(self):
        self.conn = ldap.initialize(AD_DATABASE_URI)
        self.conn.protocol_version = LDAP_PROTOCOL_VERSION
        self.conn.set_option(ldap.OPT_REFERRALS, 0)
        self.conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT,
                             ldap.OPT_X_TLS_DEMAND)
        self.conn.set_option(ldap.OPT_X_TLS_DEMAND, True)

    def bind_ldap(self):
        self.get_ldap_connection()
        dn = "cn=%s,ou=People,dc=canvas,dc=virtue,dc=com" % (
            self.email.split("@")[0])
        try:
            self.conn.simple_bind_s(dn, self.password)
        except:
            return False
        return True

    def bind_ad(self):
        self.get_ad_connection()
        try:
            self.conn.simple_bind_s(self.email, self.password)
        except:
            return False
        return True

    def get_obj(self, prop, prop_value, objectClass=None, throw_error=False):

        try:
            search_str = '({0}={1})'.format(prop, prop_value)

            if (objectClass != None):
                search_str = '(&{0}(objectClass={1}))'.format(
                    search_str, objectClass)

            r = self.conn.search_s( LDAP_VIRTUE_DN, ldap.SCOPE_SUBTREE, \
                    search_str )

            #for k in r[0][1].keys():
            #    print( "{0}, {1}".format( k, r[0][1][k] ) )

            if (len(r) == 0):
                return ()

            return r[0][1]
        except Exception as e:
            print("Error: {0}".format(e))
            # Send error to calling function if indicated
            if (throw_error):
                raise e
            return None

    def get_objs_of_type(self, objectClass):

        try:
            r = self.conn.search_s( LDAP_VIRTUE_DN, ldap.SCOPE_SUBTREE, \
                    '(objectClass={0})'.format( objectClass ) )

            return r
        except Exception as e:
            print("Error: {0}".format(e))
            return None

    def add_obj(self, obj, parent_rdn, identifier, throw_error=False):

        try:
            if (identifier not in obj):
                return 22  # EINVAL

            r = self.conn.search_s( LDAP_VIRTUE_DN, ldap.SCOPE_SUBTREE, \
                    '({0}={1})'.format( identifier, obj[identifier] ) )

            for i in r:
                if (identifier in i[0].split(',')[0]):
                    # Object with identifier already exists
                    return 22  # EINVAL

            modlist = ldap.modlist.addModlist(obj)

            self.conn.add_s(
                '{0}={1},cn={2},{3}'.format(identifier, obj[identifier],
                                            parent_rdn, LDAP_VIRTUE_DN),
                modlist)

            return 0  # Success!

        except Exception as e:
            print("Error: {0}".format(e))
            # Send error to calling function if indicated
            if (throw_error):
                raise e
            return None

    def modify_obj(self,
                   prop,
                   prop_value,
                   new,
                   objectClass=None,
                   throw_error=False):

        try:
            search_str = '({0}={1})'.format(prop, prop_value)

            if (objectClass != None):
                search_str = '(&{0}(objectClass={1}))'.format(
                    search_str, objectClass)

            r = self.conn.search_s( LDAP_VIRTUE_DN, ldap.SCOPE_SUBTREE, \
                    search_str )

            if (len(r) != 1):
                # We only want to change it if there's no
                # possibility that we're referring to the wrong object.
                return 22  # Error EINVAL

            dn = r[0][0]
            curr = r[0][1]

            # modlist = ldap.modlist.modifyModlist( r[0][1], new )
            modlist = []
            for k in new:
                if (curr.get(k) == None and new.get(k) != None):
                    modlist.append((0, k, new[k]))
                elif (curr.get(k) != None and new.get(k) != None
                      and new[k] != curr[k]):
                    modlist.append((2, k, new[k]))

            self.conn.modify_s(dn, modlist)

            return 0  # Success!

        except Exception as e:
            print("Error: {0}".format(e))
            # Send error to calling function if indicated
            if (throw_error):
                raise e
            return None

    def del_obj(self, prop, prop_value, objectClass=None, throw_error=False):

        try:
            search_str = '({0}={1})'.format(prop, prop_value)

            if (objectClass != None):
                search_str = '(&{0}(objectClass={1}))'.format(
                    search_str, objectClass)

            r = self.conn.search_s( LDAP_VIRTUE_DN, ldap.SCOPE_SUBTREE, \
                    search_str )

            if (len(r) != 1):
                # We only want to delete it if there's no
                # possibility that we're referring to the wrong object.
                return 22  # Error EINVAL

            dn = r[0][0]
            self.conn.delete_s(dn)

            return 0  # Success
        except Exception as e:
            print("Error: {0}".format(e))
            # Send error to calling function if indicated
            if (throw_error):
                raise e
            return None

    def query_ldap(self, prop, prop_value):
        try:
            r = self.conn.search_s(LDAP_QUERY_DN, ldap.SCOPE_SUBTREE,
                                   '(%s=%s)' % (prop, prop_value), ['cn'])
            return r[0][1]
        except:
            print('Conn Error')

    def query_ad(self, prop, prop_value):
        try:
            r = self.conn.search_s(AD_QUERY_DN, ldap.SCOPE_SUBTREE,
                                   '(%s=%s)' % (prop, prop_value), ['cn'])
            return r[0][1]
        except:
            print('Conn Error')


if __name__ == "__main__":
    user = LDAP('klittle@virtue.com', 'Test123!')
    user.bind_ad()
    print user.query_ad('userPrincipalName', 'klittle@virtue.com')

    user2 = LDAP('jmitchell@virtue.com', 'Test123!')
    user2.bind_ldap()
    print user2.query_ldap('cn', 'jmitchell')
