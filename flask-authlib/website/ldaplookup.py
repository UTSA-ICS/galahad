import ldap

LDAP_DATABASE_URI = "ldap://ip-172-30-1-44.ec2.internal"
AD_DATABASE_URI = "ldap://EC2AMAZ-UPCI42G.virtue.com"
LDAP_PROTOCOL_VERSION = 3
LDAP_QUERY_DN = "dc=canvas,dc=virtue,dc=com"
AD_QUERY_DN = "ou=virtue,dc=virtue,dc=com"

class LDAP():

    email = None
    password = None
    conn = None

    def __init__(self, email, password):
        self.email = email
        self.password = password

    def get_ldap_connection(self):
        self.conn = ldap.ldapobject.ReconnectLDAPObject(LDAP_DATABASE_URI)
        self.conn.protocol_version = LDAP_PROTOCOL_VERSION

    def get_ad_connection(self):
        self.conn = ldap.ldapobject.ReconnectLDAPObject(AD_DATABASE_URI)
        self.conn.protocol_version = LDAP_PROTOCOL_VERSION
        self.conn.set_option(ldap.OPT_REFERRALS, 0)

    def bind_ldap(self):
        self.get_ldap_connection()
        dn = "cn=%s,ou=People,dc=canvas,dc=virtue,dc=com" % (self.email.split("@")[0])
        try:
            self.conn.simple_bind_s(dn, self.password)
        except:
            return False
        return self.conn

    def bind_ad(self):
        self.get_ad_connection()
        try:
            self.conn.simple_bind_s(self.email, self.password)
        except:
            return False
        return self.conn

    def query_ldap(self, prop, prop_value):
        try:
            r = self.conn.search_s(LDAP_QUERY_DN, ldap.SCOPE_SUBTREE, '(%s=%s)' % (prop, prop_value), ['cn'])
            return r[0][1]
        except:
            print ('Conn Error')

    def query_ad(self, prop, prop_value):
        try:
            r = self.conn.search_s(AD_QUERY_DN, ldap.SCOPE_SUBTREE, '(%s=%s)' % (prop, prop_value), ['cn'])
            return r[0][1]
        except:
            print ('Conn Error')

if __name__ == "__main__":
    user = LDAP('klittle@virtue.com', 'Test123!')
    user.bind_ad()
    print user.query_ad('userPrincipalName', 'klittle@virtue.com')

    user2 = LDAP('jmitchell@virtue.com', 'Test123!')
    user2.bind_ldap()
    print user2.query_ldap('cn', 'jmitchell')
