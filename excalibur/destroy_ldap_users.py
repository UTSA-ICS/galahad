#!/usr/bin/python

import argparse
import sys

from website import ldap_tools
from website.ldaplookup import LDAP

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--delete_user",
                        help="Specify the LDAP User to delete")
    parser.add_argument("-a", "--delete_all_users", action="store_true",
                        help="Delete All LDAP Users")
    parser.add_argument("-l", "--list_users", action="store_true",
                        help="List All LDAP Users")

    args = parser.parse_args()

    inst = LDAP('', '')
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s(dn, 'Test123!')

    if args.delete_user:
        msg = raw_input(
            "This is a permanent change and cannot be undone. Are you "
            "sure you want to continue?\n[Y/N]")
        if msg != "Y":
            print("Aborted Deletion...")
            sys.exit()
        print('Deleting user [{}]'.format(args.delete_user))
        inst.del_obj('cusername', args.delete_user, objectClass='OpenLDAPUser')
    else:
        users = inst.get_objs_of_type('OpenLDAPUser')
        users = ldap_tools.parse_ldap_list(users)

        if args.delete_all_users:
            msg = raw_input(
                "This is a permanent change and cannot be undone. Are you "
                "sure you want to continue?\n[Y/N]")
            if msg != "Y":
                print("Aborted Deletion...")
                sys.exit()
            print('Deleting ALL users')
            for user in users:
                print('Deleting user [{}]'.format(user['username']))
                inst.del_obj('cusername', user['username'],
                             objectClass='OpenLDAPUser')
        elif args.list_users:
            print('Listing ALL users in LDAP')
            for user in users:
                print(' Username - [{}]'.format(user['username']))
        else:
            parser.print_help()
