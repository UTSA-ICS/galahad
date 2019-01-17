#!/usr/bin/python

from ldaplookup import LDAP
import ldap_tools
import ldap

ad = LDAP('slapd@virtue.gov', 'Test123!')
ad.bind_ad()
ad_users = ad.query_ad('objectClass', 'user')

dn = "cn=admin,dc=canvas,dc=virtue,dc=com"
ldap = LDAP('', '')
ldap.get_ldap_connection()
ldap.conn.simple_bind_s(dn, "Test123!")
ldap_users = ldap_tools.parse_ldap_list(ldap.get_objs_of_type('OpenLDAPuser'))

usernames = []
for user in ldap_users:
    usernames.append(user['username'])

for user in ad_users:
    username = user[1]['cn'][0]
    if username not in usernames:
        user = {'username': username, 'authorizedRoleIds': []}
        ldap_user = ldap_tools.to_ldap(user, 'OpenLDAPuser')
        ldap.add_obj(ldap_user, 'users', 'cusername', throw_error=True)
