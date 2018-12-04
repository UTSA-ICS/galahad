#!/usr/bin/python3

import os
import sys
import shutil
import time
import json
import subprocess
import argparse
import requests
import copy
import getpass
import base64
import itertools
from enum import Enum
from zipfile import ZipFile

from sso_login import sso_tool
from firefox_full_plugin import FirefoxPlugin

DEFAULT_EXCALIBUR_PORT = 5002
DEFAULT_APP_NAME = 'APP_1'
OAUTH_REDIRECT = 'https://{0}/virtue/test'

# TODO: Remove calls to user API (Currently, virtue launch is the only one)

class Packager():

    def __init__(self, excalibur_ip, access_token):
        self.excalibur_ip = excalibur_ip
        self.access_token = access_token

        self.session = requests.Session()
        self.session.headers = {
            'Authorization': 'Bearer {0}'.format(access_token)
        }
        self.session.verify = False

        self.base_url = 'https://{0}/virtue'.format(ip)

    def export_virtue(self, virtue_id, plugins, output_path):

        admin_url = 'https://{0}/virtue/admin'.format(self.excalibur_ip)
        security_url = 'https://{0}/virtue/security'.format(self.excalibur_ip)

        # get admin's notes
        admin_notes = input('Notes (Optional): ')

        timestamp = int(time.time())

        galahad_id = self.session.get(
            '{0}/galahad/get/id'.format(admin_url)).json()

        virtue = self.get_virtue(virtue_id)

        role = self.get_role(virtue['roleId'])

        apps = self.session.get('{0}/application/list'.format(admin_url)).json()

        role_apps = []
        for app in apps:
            if app['id'] in role['applicationIds']:
                role_apps.append(app)

        enabled_transducer_ids = self.session.get(
            '{0}/transducer/list_enabled'.format(security_url),
            params={'virtueId': virtue['id']}).json()

        if (self.is_error(enabled_transducer_ids)):
            return

        enabled_transducers = []
        for transducer_id in enabled_transducer_ids:

            t = self.session.get(
                '{0}/transducer/get'.format(security_url),
                params={'transducerId': transducer_id}).json()

            if (not self.is_error(t)):
                enabled_transducers.append(t)

        transducer_data = []
        for transducer in enabled_transducers:

            config = self.session.get(
                '{0}/transducer/get_configuration'.format(security_url),
                params={'transducerId': transducer['id'],
                        'virtueId': virtue_id}).json()

            self.is_error(config)

            transducer['config'] = config
            transducer_data.append({'id': transducer['id'],
                                    'config': config})

        work_dir = '/tmp/.{0}_export'.format(virtue_id)
        config_dir = work_dir + '/app_configs'
        tmp_pkg_path = work_dir + '/zippity.zip'
        os.makedirs(work_dir, exist_ok=True)
        os.makedirs(config_dir, exist_ok=True)
        os.makedirs(work_dir + '/tmp', exist_ok=True)

        try:
            os.remove(tmp_pkg_path)
        except:
            pass

        plugin_data = {}
        downloaded_configs = []
        for plugin in plugins:

            for app_id in plugin.get_required_app_configs(role_apps):
                if (app_id not in downloaded_configs):

                    self.retrieve_config(
                        virtue['username'],
                        virtue['roleId'],
                        app_id,
                        config_dir,
                        work_dir + '/tmp')

                    downloaded_configs.append(app_id)

            with FileInterface(tmp_pkg_path,
                               config_dir,
                               plugin.id,
                               virtue_id,
                               downloaded_configs,
                               mode=FileInterface.Mode.EXPORT) as file_interface:
                plugin_object = plugin(file_interface)
                plugin_data[plugin.id] = plugin_object.export_virtue(
                    virtue_id,
                    role_apps)

        package_json = {
            'notes': admin_notes,
            'galahadId': galahad_id,
            'timeCreated': timestamp,
            'virtueId': virtue_id,
            'role': {
                'name': role['name'],
                'version': role['version'],
                'applicationNames': [app['name'] for app in role_apps],
            },
            'transducerData': transducer_data,
            'securityProfile': None,
            'user': {
                'username': virtue['username']
            },
            'plugins': plugin_data
        }

        print()
        print(package_json)

        with ZipFile(tmp_pkg_path, 'a') as package:
            with package.open(virtue['id'] + '/metadata.json', 'w') as f:
                f.write(json.dumps(package_json).encode())

        # We're done gathering data. Sign it and send it off!

        # TODO: Sign zip file

        shutil.copy(tmp_pkg_path, output_path)

    @staticmethod
    def interrogate_package(package_path, plugins):

        # TODO: Check package signature

        # Pretty-print JSON contents
        metadata = Packager.get_metadata_from_package(package_path)
        print('Package Metadata:')
        print(json.dumps(metadata, indent=4, sort_keys=True))

        print()

        # Tree the package files
        with ZipFile(package_path, 'r') as zip_file:
            namelist = zip_file.namelist()

        print('Package file structure:')
        for line in namelist:

            # Don't include the ending / when checking
            if (line[0:-1].count('/') < 3):
                print(line)

        for plugin in plugins:

            print()

            if (plugin.id not in metadata['plugins'].keys()):
                continue

            print('Plugin:')
            print('  ID: ' + plugin.id)
            print('  Name: ' + plugin.name)
            print('  Version: ' + plugin.version_str)
            print('  Description: ' + plugin.description)
            print('Plugin Output:')

            with FileInterface(package_path,
                               '/dev/null',
                               plugin.id,
                               metadata['virtueId'],
                               None) as file_interface:
                p = plugin(file_interface)
                p.interrogate_package(metadata['plugins'][plugin.id])

    def import_virtue(self, package_path, username, plugins, role_id=None):

        # TODO: Check package signature

        metadata = self.get_metadata_from_package(package_path)

        admin_url = 'https://{0}/virtue/admin'.format(self.excalibur_ip)
        security_url = 'https://{0}/virtue/security'.format(self.excalibur_ip)

        print('Package Notes: {0}'.format(metadata['notes']))

        users = self.session.get('{0}/user/list'.format(admin_url)).json()
        assert username in [user['username'] for user in users]

        apps = self.session.get('{0}/application/list'.format(admin_url)).json()
        
        roles = self.session.get('{0}/role/list'.format(admin_url)).json()

        matching_role = None
        if (role_id != None):
            for role in roles:
                if (role['id'] == role_id):
                    matching_role = role

        else:
            matching_role = self.find_matching_role(roles, metadata['role'])

        new_apps = []
        for app_name in metadata['role']['applicationNames']:

            new_apps.append(None)
            for app in apps:
                if (app['name'] == app_name
                    and app not in new_apps
                    and (new_apps[-1] == None
                         or app['version'] > new_apps[-1]['version'])):
                    new_apps[-1] = app

            if (new_apps[-1] == None):
                new_apps.remove(None)

        new_role = {
            'name': metadata['role']['name'],
            'version': metadata['role']['version'],
            'applicationIds': [app['id'] for app in new_apps],
            'startingResourceIds': [],
            'startingTransducerIds': [t['id'] for t in metadata['transducerData']]
        }

        create_role = False
        import_role = None
        if (matching_role == None):

            create_role = ask_yes_or_no(
                ('No matching role found.\n{0}\n'
                 'Create a new role with the above'
                 ' configuration?').format(json.dumps(
                     new_role, indent=4, sort_keys=True)),
                default=False)
        else:

            ans = ask_yes_or_no(
                ('Found role:\n{0}\nWould you like to import'
                 ' with this existing role?').format(json.dumps(
                     matching_role, indent=4, sort_keys=True)))
            if (ans):
                import_role = matching_role
            else:
                matching_role = None
                create_role = ask_yes_or_no(
                    ('{0}\nCreate new role with the above'
                     ' configuration?').format(json.dumps(
                         new_role, indent=4,
                         sort_keys=True)),
                    default=False)

        spinner = itertools.cycle(['|', '/', '-', '\\'])

        if (create_role == False and matching_role == None):
            return
        elif (create_role == True):

            role = self.session.get('{0}/role/create'.format(admin_url),
                                    params={'role': json.dumps(new_role)}).json()

            if (self.is_error(role)):
                return

            print('New Role ID: {0}'.format(role['id']))

            role['state'] = 'CREATING'

            sys.stdout.write('\n\t ')
            sys.stdout.flush()
            while (role['state'] == 'CREATING'):

                time.sleep(1)

                role = self.get_role(role['id'])

                sys.stdout.write('\b' + next(spinner))
                sys.stdout.flush()

            print()
            print()

            if (role['state'] != 'CREATED'):
                print("role['state'] = " + role['state'])

            import_role = new_role
            import_role['id'] = role['id']

        self.session.get('{0}/user/role/authorize'.format(admin_url),
                         params={'username': username,
                                 'roleId': import_role['id']})

        work_dir = '/tmp/.{0}_import'.format(metadata['virtueId'])
        config_dir = work_dir + '/config'
        os.makedirs(config_dir, exist_ok=True)
        os.makedirs(work_dir + '/tmp', exist_ok=True)

        for f in os.listdir(config_dir):
            shutil.rmtree(os.path.join(config_dir, f))

        for plugin in plugins:

            if (plugin.id not in metadata['plugins'].keys()):
                continue

            with FileInterface(package_path,
                               config_dir,
                               plugin.id,
                               metadata['virtueId'],
                               [app['id'] for app in apps],
                               mode=FileInterface.Mode.IMPORT) as file_interface:
                p = plugin(file_interface)

                p.import_virtue(
                    "virtue['id']",
                    metadata['plugins'][plugin.id],
                    apps)

        for app_id in [app['id'] for app in apps]:

            if (os.path.isdir(os.path.join(config_dir, app_id))):

                # There's config data for this app. Send it to Excalibur.
                shutil.make_archive(work_dir + '/tmp/' + app_id,
                                    'zip',
                                    config_dir,
                                    app_id)

                with open('{0}/tmp/{1}.zip'.format(work_dir, app_id), 'rb') as z:
                    zip_data = base64.b64encode(z.read())

                response = self.session.get(
                    '{0}/import_app_config'.format(admin_url),
                    params={
                        'username': username,
                        'roleId': role['id'],
                        'applicationId': app_id,
                        'zipData': zip_data
                    })
                if (response.status_code != 200):
                    print(response.text)

        virtue = self.session.get(
            '{0}/virtue/create'.format(admin_url),
            params={'username': username,
                    'roleId': import_role['id']}).json()

        if (self.is_error(virtue)):
            return

        print('New Virtue ID: ' + virtue['id'])

        virtue['state'] = 'CREATING'

        sys.stdout.write('\n\t ')
        sys.stdout.flush()
        while (virtue['state'] == 'CREATING'):

            time.sleep(1)

            virtue = self.get_virtue(virtue['id'], username)

            sys.stdout.write('\b' + next(spinner))
            sys.stdout.flush()

        print()
        print()

        if (virtue['state'] != 'STOPPED'):
            print("virtue['state'] = " + virtue['state'])
            return

        response = self.session.get(
            '{0}/user/virtue/launch'.format(self.base_url),
            params={'virtueId': virtue['id']})

        print(response.json())

        running_transducer_ids = self.session.get(
            '{0}/transducer/list_enabled'.format(security_url),
            params={'virtueId': virtue['id']}).json()

        if (self.is_error(running_transducer_ids)):
            return

        for transducer_id in running_transducer_ids:

            response = self.session.get(
                '{0}/transducer/disable'.format(security_url),
                params={'transducerId': transducer_id,
                        'virtueId': virtue['id']}).json()
            self.is_error(response)

        all_transducers = self.session.get('{0}/transducer/list'.format(
            security_url))

        for t in metadata['transducerData']:

            response = self.session.get(
                '{0}/transducer/enable'.format(security_url),
                params={'transducerId': t['id'],
                        'virtueId': virtue['id'],
                        'configuration': json.dumps(t['config'])}).json()
            self.is_error(response)

    @staticmethod
    def is_error(response):

        if (type(response) == list
            and type(response[0]) == int
            and type(response[1]) == str):

            print('Error: {0}'.format(response))
            return True

        return False

    def get_role(self, role_id):

        roles = self.session.get(self.base_url + '/admin/role/list').json()

        for role in roles:
            if (role['id'] == role_id):
                return role

        return None

    def get_virtue(self, virtue_id, username=None):

        if (username == None):
            users =  self.session.get(self.base_url + '/admin/user/list').json()
        else:
            users = [{'username': username}]

        for user in users:
            virtues = self.session.get(
                '{0}/admin/user/virtue/list'.format(self.base_url),
                params={'username': user['username']}).json()

            for virtue in virtues:
                if (virtue['id'] == virtue_id):
                    return virtue

        return None

    @staticmethod
    def get_metadata_from_package(package_path):

        # Load JSON data
        with ZipFile(package_path, 'r') as zip_file:

            first_dir = zip_file.namelist()[0]

            while (os.path.dirname(first_dir) != ''):
                first_dir = os.path.dirname(first_dir)

            json_txt = ''
            with zip_file.open(first_dir + '/metadata.json') as meta_file:
                json_txt = meta_file.read().decode()

            return json.loads(json_txt)

    def retrieve_config(self, user, roleId, app_id, config_dir, zip_dir):

        print('Getting config for {0}'.format(app_id))
        data = self.session.get(
            '{0}/admin/export_app_config'.format(self.base_url),
            params={'username': user,
                    'roleId': roleId,
                    'applicationId': app_id})

        with open('{0}/{1}.zip'.format(zip_dir,
                                       app_id), 'wb') as f:
            f.write(base64.b64decode(data.json()))

        with ZipFile('{0}/{1}.zip'.format(zip_dir, app_id)) as zip_file:

            commonpath = os.path.commonpath(zip_file.namelist())
            assert (commonpath == app_id or commonpath.startswith(app_id + '/'))

            if (os.path.exists(config_dir + '/' + app_id)):
                shutil.rmtree(config_dir + '/' + app_id)
            
            zip_file.extractall(config_dir)

    def find_matching_role(self, search_roles, role_data):

        roles = copy.deepcopy(search_roles)
        target_role = copy.deepcopy(role_data)

        target_role['name'] = target_role['name'].lower()
        target_role['version'] = target_role['version'].lower()

        for i in range(len(target_role['applicationNames'])):
            target_role['applicationNames'][i] = \
                target_role['applicationNames'][i].lower()

        apps = self.session.get(self.base_url + '/admin/application/list').json()

        app_id_to_name = {}
        for app in apps:
            app_id_to_name[app['id']] = app['name'].lower()

        best_fit_role = None
        for role in roles:

            if (best_fit_role):
                print(best_fit_role['id'])
            else:
                print('None')

            role['appNames'] = []
            for app_id in role['applicationIds']:
                role['appNames'].append(app_id_to_name[app_id])

            matching_apps = set(target_role['applicationNames']) == set(
                role['appNames'])
            matching_names = role['name'].lower() == target_role['name']
            matching_versions = role['version'].lower() == target_role['version']

            if (matching_apps and matching_names):
                best_fit_role = role
                if (matching_versions):
                    break
                continue
            elif (best_fit_role != None
                  and best_fit_role['name'].lower() == target_role['name']
                  and set(best_fit_role['appNames']) == set(
                      target_role['applicationNames'])):
                continue

            if (matching_names):
                if (best_fit_role == None):
                    best_fit_role = role
                    continue
                elif (best_fit_role['name'].lower() != target_role['name']
                      or best_fit_role['version'].lower() != target_role['version']):
                    best_fit_role = role
                    continue

            if (matching_apps):
                if (best_fit_role == None):
                    best_fit_role = role
                elif (set(best_fit_role['appNames']) == set(
                        target_role['applicationNames'])
                      and best_fit_role['name'].lower() != target_role['name']):
                    best_fit_role = role

        if (best_fit_role != None):
            del best_fit_role['appNames']

        print('Matching role: {0}'.format(best_fit_role['id']))

        return best_fit_role

    def discover_plugins(self, directory):
        pass

class FileInterface():

    class Mode(Enum):
        EXPORT = 0
        IMPORT = 1
        INTERROGATE = 2

    def __init__(self, package_path, config_path, plugin_id, virtue_id, apps,
                 mode=Mode.INTERROGATE):

        self.check_paths(plugin_id)
        
        self.package_path = package_path
        self.config_path = config_path
        self.plugin_id = plugin_id
        self.virtue_id = virtue_id
        self.app_ids = apps
        ''' self.mode =
                EXPORT (package read/write virtue read-only
                INTERROGATE (package read-only)
                IMPORT (package read-only virtue read/write
        '''

        if (mode == self.Mode.EXPORT):
            zip_mode = 'a'
        else:
            zip_mode = 'r'

        self.mode = mode

        self.zip_file = ZipFile(package_path, zip_mode)

    def list_package_files(self, pkg_subdir=None):

        if (pkg_subdir == None):
            pkg_subdir = self.plugin_id

        self.check_paths(pkg_subdir)

        base_dir = os.path.join(self.virtue_id, pkg_subdir)

        namelist = self.zip_file.namelist()

        paths = []
        for path in namelist:
            if (not path.startswith(base_dir)):
                del path
                continue

            # Note while using os.path.relpath:
            #   relpath(a, b) returns a path to get
            #   from b to a, not a to b
            relpath = os.path.relpath(path, base_dir)
            if (relpath != '.'):
                paths.append(relpath)

        return paths

    # Not callable during interrogation
    def list_virtue_files(self, app_id):

        if (self.mode == self.Mode.INTERROGATE):
            raise Exception("Can't list virtue files while interrogating.")

        assert app_id in self.app_ids

        base_dir = os.path.join(self.config_path, app_id)

        paths = []
        for path, dirs, files in os.walk(base_dir):

            for d in dirs:
                relpath = os.path.relpath(os.path.join(path, d), base_dir)
                paths.append(relpath + '/')

            for f in files:
                relpath = os.path.relpath(os.path.join(path, f), base_dir)
                paths.append(relpath)

        return paths

    def open_package_file(self, path, mode='r', pkg_subdir=None):

        if ((self.mode == self.Mode.INTERROGATE
             or self.mode == self.Mode.IMPORT)
            and 'w' in mode):
            raise Exception('Can only write to package while exporting.')

        if (pkg_subdir == None):
            pkg_subdir = self.plugin_id

        self.check_paths(path, pkg_subdir)

        pkg_path = os.path.join(self.virtue_id, pkg_subdir, path)

        return self.zip_file.open(pkg_path, mode)

    def open_virtue_file(self, path, app_id, mode='r'):

        if (self.mode == self.Mode.INTERROGATE):
            raise Exception("Can't open virtue file while interrogating.")

        if (self.mode == self.Mode.IMPORT
            and 'w' in mode):
            raise Exception("Can only write to virtue while importing.")

        self.check_paths(path)
        assert app_id in self.app_ids

        file_path = os.path.join(self.config_path, app_id, path)

        if ('w' in mode):
            os.path.makedirs(os.path.dirname(file_path), exist_ok=True)

        return open(file_path, mode)

    # Only callable while exporting
    def copy_to_package(self, src, dst, app_id, recursive=False):

        if (self.mode != self.Mode.EXPORT):
            raise Exception('Can only write to package while exporting.')

        assert app_id in self.app_ids

        self.check_paths(src, dst)

        src_path = os.path.normpath(os.path.join(self.config_path, app_id, src))
        dst_path = os.path.normpath(
            os.path.join(self.virtue_id, self.plugin_id, dst))

        if (os.path.isdir(src_path)
            and not recursive):
            assert not 'dir'

        self.pkg_write(src_path, dst_path)

        if (not recursive):
            return
        
        for path, dirs, files in os.walk(src_path):

            for d in dirs:
                dir_path = os.path.join(path, d)
                relpath = os.path.relpath(dir_path, src_path)

                self.pkg_write(
                    dir_path,
                    os.path.join(dst_path, relpath))

            for f in files:
                file_path = os.path.join(path, f)
                relpath = os.path.relpath(file_path, src_path)

                self.pkg_write(
                    file_path,
                    os.path.join(dst_path, relpath))

    # Only callable while importing
    def copy_from_package(self, src, dst, app_id, recursive=False, pkg_subdir=None):

        if (self.mode != self.Mode.IMPORT):
            raise Exception('Can only write to virtue while importing.')

        if (pkg_subdir == None):
            pkg_subdir = self.plugin_id

        assert app_id in self.app_ids

        self.check_paths(src, dst, pkg_subdir)

        app_dir = os.path.join(self.config_path, app_id)

        if (not os.path.isdir(app_dir)):
            os.mkdir(os.path.join(self.config_path, app_id))

        src_path = os.path.normpath(
            os.path.join(self.virtue_id, pkg_subdir, src))
        dst_path = os.path.normpath(os.path.join(app_dir, dst))

        # os.path.normpath() eliminates trailing '/'s
        if (src_path not in self.zip_file.namelist()
            and src_path + '/' in self.zip_file.namelist()):
            if (not recursive):
                assert not 'dir'
            src_path = src_path + '/'

        p = self.zip_file.extract(src_path, self.config_path + '/../tmp')
        if (not os.path.samefile(app_dir, dst_path)):
            os.rename(p, dst_path)

        if (not recursive):
            return

        for path in self.zip_file.namelist():
            if (not path.startswith(src_path) or path == src_path):
                continue

            f = self.zip_file.extract(path, self.config_path + '/../tmp')
            d = os.path.join(dst_path, os.path.relpath(path, src_path))
            try:
                os.rename(f, os.path.normpath(d))
            except OSError:
                pass

    @staticmethod
    def check_paths(*args):
        for arg in args:
            assert not os.path.normpath(arg).startswith('..')
            assert not os.path.normpath(arg).startswith('/')

    def pkg_write(self, filename, arcname):
        assert arcname not in self.zip_file.namelist()
        self.zip_file.write(filename, arcname=arcname)

    def close(self):
        self.zip_file.close()

    def __enter__(self):
        return self

    def __exit__(self, thing1, thing2, thing3):
        self.close()

def ask_yes_or_no(question, default=True):

    if (default):
        ans = input('{0} [Y/n] '.format(question))
    else:
        ans = input('{0} [y/N] '.format(question))

    print()

    if (ans.strip().lower().startswith('y')):
        return True
    elif (ans.strip().lower().startswith('n')):
        return False

    return default

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-e',
        '--excalibur_ip',
        type=str,
        required=True,
        help='The IP address of an existing aws excalibur instance')
    parser.add_argument(
        '-p',
        '--excalibur_port',
        type=int,
        required=False,
        default=DEFAULT_EXCALIBUR_PORT,
        help='The port number that the excalibur instance is listening on')
    parser.add_argument(
        '-u',
        '--user',
        type=str,
        required=False,
        default=None,
        help='The user to login with')
    parser.add_argument(
        '--password',
        type=str,
        required=False,
        default=None,
        help='The password to login with (plaintext security hazard)')
    parser.add_argument(
        '-a',
        '--oauth_app',
        type=str,
        required=False,
        default=DEFAULT_APP_NAME,
        help='The OAuth App name to login with')

    parser.add_argument(
        '-o',
        '--output_path',
        type=str,
        required=False,
        default=None,
        help='The path for the new Package')
    parser.add_argument(
        '-r',
        '--role',
        type=str,
        required=False,
        default=None,
        help='The role ID to import with')
    parser.add_argument(
        '-i',
        '--user_for_import',
        type=str,
        required=False,
        default=None,
        help='The user to give the imported virtue')
    
    parser.add_argument(
        '--export',
        type=str,
        required=False,
        default=None,
        help='Export the specified Virtue')
    parser.add_argument(
        '--interrogate',
        type=str,
        required=False,
        default=None,
        help='Summarize the contents of the specified Package')
    parser.add_argument(
        '--import_',
        type=str,
        required=False,
        default=None,
        help='Import the specified Package')

    arg = parser.parse_args()

    return arg

if (__name__ == '__main__'):

    args = parse_args()

    if (args.interrogate):
        Packager.interrogate_package(args.interrogate, [FirefoxPlugin])

    if (not args.export and not args.import_):
        exit(0)

    if (args.excalibur_ip == None):
        print('Need -e/--excalibur_ip argument to import/export')
        exit(1)

    ip = args.excalibur_ip + ':' + str(args.excalibur_port)

    redirect = OAUTH_REDIRECT.format(ip)

    sso = sso_tool(ip)

    username = args.user
    if (username == None):
        username = input('Username: ')

    password = args.password
    if (password == None):
        password = getpass.getpass('Password: ')
    assert sso.login(username, password)

    del args.password
    del password

    oauth_app = args.oauth_app
    if (oauth_app == DEFAULT_APP_NAME):
        oauth_app = input("OAuth APP name "
                          "(Default name '{0}' Press Enter): "
                          "".format(DEFAULT_APP_NAME))

    client_id = sso.get_app_client_id(oauth_app)
    if (client_id == None):
        client_id = sso.create_app(oauth_app, redirect)
        assert client_id

    code = sso.get_oauth_code(client_id, redirect)
    assert code

    token = sso.get_oauth_token(client_id, code, redirect)
    assert 'access_token' in token

    # TODO: Get plugins

    pkger = Packager(ip, token['access_token'])

    if (args.export):
        if (args.output_path == None):
            output_path = 'package.zip'
        else:
            output_path = args.output_path

        pkger.export_virtue(args.export, [FirefoxPlugin], output_path)

    if (args.import_):
        if (args.user_for_import == None):
            print('Need -i/--user_for_import argument to import')
            exit(1)

        pkger.import_virtue(args.import_, args.user_for_import, [FirefoxPlugin], role_id=args.role)
