#!/usr/bin/python

import os
import sys
import shutil
import json
import ldap
import ldap.modlist

file_path = os.path.realpath(__file__)
base_excalibur_dir = os.path.dirname(
    os.path.dirname(file_path)) + '/../../excalibur'
sys.path.insert(0, base_excalibur_dir)
from website.ldaplookup import LDAP
from website.ldap_tools import to_ldap

LDAP_VIRTUE_DN = "ou=virtue,dc=canvas,dc=virtue,dc=com"


def add_subtree(name, gid):

    tree = ldap.modlist.addModlist({
        'objectClass': ['top', 'posixGroup'],
        'gidNumber': str(gid),
        'cn': name
    })

    inst.conn.add_s('cn={0},{1}'.format(name, LDAP_VIRTUE_DN), tree)


def add_person(cn, sn, password):

    dn = 'cn={0},ou=People,dc=canvas,dc=virtue,dc=com'.format(cn)

    user = ldap.modlist.addModlist({
        'objectClass': ['simpleSecurityObject', 'inetOrgPerson'],
        'cn':
        cn,
        'sn':
        sn,
        'userPassword':
        password
    })

    inst.conn.add_s(dn, user)


def add_application(
    id,
    name,
    version,
    os,
    port=None):

    app = {
        'id': id,
        'name': name,
        'version': version,
        'os': os
    }

    if (port != None):
        app['port'] = int(port)

    ldap_app = to_ldap(app, 'OpenLDAPapplication')

    inst.add_obj(ldap_app, 'applications', 'cid', throw_error=True)


def add_resource(id, type, unc, credentials):

    res = {'id': id, 'type': type, 'unc': unc, 'credentials': credentials}

    ldap_res = to_ldap(res, 'OpenLDAPresource')

    inst.add_obj(ldap_res, 'resources', 'cid', throw_error=True)


def add_role(id, name, version, appIds, resIds, transIds, state='CREATED'):

    role = {
        'id': id,
        'name': name,
        'version': version,
        'applicationIds': appIds,
        'startingResourceIds': resIds,
        'startingTransducerIds': transIds,
        'state': state
    }

    if (type(appIds) == str):
        role['applicationIds'] = json.loads(appIds)

    if (type(resIds) == str):
        role['startingResourceIds'] = json.loads(resIds)

    if (type(transIds) == str):
        role['startingTransducerIds'] = json.loads(transIds)

    ldap_role = to_ldap(role, 'OpenLDAProle')

    inst.add_obj(ldap_role, 'roles', 'cid', throw_error=True)


def add_transducer(id_, name, type_, startEnabled, startingConfiguration,
                   requiredAccess):

    transducer = {
        'id': id_,
        'name': name,
        'type': type_,
        'startEnabled': startEnabled,
        'startingConfiguration': startingConfiguration,
        'requiredAccess': requiredAccess
    }

    if (type(startingConfiguration) == str):
        transducer['startingConfiguration'] = json.loads(startingConfiguration)

    if (type(requiredAccess) == str):
        transducer['requiredAccess'] = json.loads(requiredAccess)

    ldap_transducer = to_ldap(transducer, 'OpenLDAPtransducer')

    inst.add_obj(ldap_transducer, 'transducers', 'cid', throw_error=True)


def add_user(username, authRoleIds):

    user = {
        'username': username,
        'authorizedRoleIds': authRoleIds
    }

    if (type(authRoleIds) == str):
        user['authorizedRoleIds'] = json.loads(authRoleIds)

    ldap_user = to_ldap(user, 'OpenLDAPuser')

    inst.add_obj(ldap_user, 'users', 'cusername', throw_error=True)

    if (not os.path.exists('{0}/galahad-keys'.format(os.environ['HOME']))):
        os.mkdir('{0}/galahad-keys'.format(os.environ['HOME']))

    # Temporary code:
    shutil.copy('{0}/default-user-key.pem'.format(os.environ['HOME']),
                '{0}/galahad-keys/{1}.pem'.format(os.environ['HOME'], username))

    # Future code will look like this:
    '''subprocess.run(
        ['ssh-keygen', '-t', 'rsa', '-f', '~/galahad-keys/{0}.pem'.format(username),
         '-C', '"For Virtue user {0}"'.format(username), '-N', '""'],
        check=True
    )'''


if (__name__ == '__main__'):

    inst = LDAP('', '')
    dn = 'cn=admin,dc=canvas,dc=virtue,dc=com'
    inst.get_ldap_connection()
    inst.conn.simple_bind_s(dn, 'Test123!')

    virtue_ou = ldap.modlist.addModlist({
        'objectClass': ['top', 'organizationalUnit'],
        'ou':
        'virtue',
        'description':
        'VirtUE organizational unit for binding with AD'
    })

    people_ou = ldap.modlist.addModlist({
        'objectClass': ['top', 'organizationalUnit'],
        'ou':
        'People',
        'description':
        'AD People integration OU'
    })

    inst.conn.add_s(LDAP_VIRTUE_DN, virtue_ou)
    inst.conn.add_s('ou=People,dc=canvas,dc=virtue,dc=com', people_ou)

    add_subtree('applications', 205)
    add_subtree('resources', 206)
    add_subtree('roles', 207)
    add_subtree('transducers', 208)
    add_subtree('users', 209)
    add_subtree('virtues', 210)

    add_application('firefox', 'Firefox', '1.0', 'LINUX', port=6768)
    add_application('terminal', 'XTerm', '1.0', 'LINUX', port=6766)
    add_application('thunderbird', 'Thunderbird', '1.0', 'LINUX', port=6765)
    add_application('gedit', 'Editor', '1.0', 'LINUX', port=6767)
    add_application('chrome', 'Chrome', '1.0', 'LINUX', port=6764)
    add_application('powershell', 'PowerShell', '1.0', 'LINUX', port=6761)
    add_application('wincmd', 'Windows Command Line', '1.0', 'WINDOWS', port=6762)
    add_application('skype', 'Skype', '1.0', 'LINUX', port=6763)
    add_application('office-word', 'Microsoft Office Word', '1.0', 'WINDOWS', port=6769)
    add_application('office-outlook', 'Microsoft Office Outlook', '1.0', 'WINDOWS', port=6771)
    add_application('putty', 'PuTTY', '1.0', 'WINDOWS', port=6770)

    add_resource('fileshare1', 'DRIVE', '//ad.galahad.com/VirtueFileShare',
                 'token')

    add_role('emptyrole', 'EmptyRole', '1.0', '[]', '[]', '[]')

    add_user('jmitchell', '[]')
    add_user('fpatwa', '[]')
    add_user('klittle', '[]')

    #add_person('jmitchell', 'Mitchell', 'Test123!')
    #add_person('klittle', 'Little', 'Test123!')
    #add_person('jmartin', 'Martin', 'Test123!')

    add_transducer('path_mkdir', 'Directory Creation', 'SENSOR', True, '{}',
                   [])
    add_transducer('bprm_set_creds', 'Process Start', 'SENSOR', True, '{}', [])
    add_transducer('task_create', 'Thread Start', 'SENSOR', True, '{}', [])
    add_transducer('task_alloc', 'Thread Allocation', 'SENSOR', True, '{}', [])
    add_transducer('inode_create', 'File Creation', 'SENSOR', True, '{}', [])
    add_transducer('socket_connect', 'Socket Connect', 'SENSOR', True, '{}',
                   [])
    add_transducer('socket_bind', 'Socket Bind', 'SENSOR', True, '{}', [])
    add_transducer('socket_accept', 'Socket Accept', 'SENSOR', True, '{}', [])
    add_transducer('socket_listen', 'Socket Listen', 'SENSOR', True, '{}', [])
    add_transducer('create_process', 'Process Creation', 'SENSOR', True, '{}',
                   [])
    add_transducer('process_start', 'Process Start', 'SENSOR', True, '{}', [])
    add_transducer('process_died', 'Process Death', 'SENSOR', True, '{}', [])
    add_transducer('srv_create_proc', 'Process Creation', 'SENSOR', True, '{}',
                   [])
    add_transducer('open_fd', 'File Open', 'SENSOR', True, '{}', [])

    add_transducer('kill_proc', 'Kill Process', 'ACTUATOR', False, {'processes': []}, [])
    add_transducer('block_net', 'Block Network', 'ACTUATOR', False, '{}', [])
    add_transducer('migration', 'Migration', 'ACTUATOR', False, '{}', [])
    add_transducer('introspection', 'Introspection', 'ACTUATOR', False, '{}', [])
