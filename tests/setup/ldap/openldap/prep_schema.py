#!/usr/bin/python3

import os
import sys
import subprocess

base_dir = os.path.dirname(os.path.realpath(__file__))

# slapcat does not like ~ while parsing schema_convert.conf,
#  I'm using os.chdir() to make relative paths consistent.
os.chdir('{0}/galahad'.format(os.environ['HOME']))

# Call slapcat -f schema_convert.conf -F ldif_output -n 0
subprocess.run(
    [
        'slapcat', '-f', '{0}/schema_convert.conf'.format(base_dir), '-F',
        '{0}/ldif_output'.format(base_dir), '-n', '0'
    ],
    check=True)

# The .ldif file will be named with the format cn={<number>}canvas.ldif,
#     but the number may not always be the same.
ls = os.listdir(base_dir + '/ldif_output/cn=config/cn=schema')
file_path = None
for file_name in ls:
    if ('canvas.ldif' in file_name):
        file_path = base_dir + '/ldif_output/cn=config/cn=schema/' + file_name
        break

if (file_path == None):
    exit(2)

with open(file_path, 'r') as before, open(base_dir + '/cn=canvas.ldif',
                                          'w') as after:
    for line in before:
        if (line[0] == '#'):
            # Skip comments
            continue
        elif ('dn: cn={' in line):
            # Replace the dn of the schema
            after.write('dn: cn=canvas,cn=schema,cn=config\n')
        elif ('cn: {' in line):
            # Clear out the {14} from the cn
            after.write('cn: canvas\n')
        elif ('structuralObjectClass: ' in line):
            # Exclude the lines at the end
            break
        else:
            # Copy/paste the rest
            after.write(line)
