#!/usr/bin/env python

# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

import os.path
import rethinkdb as r
import sys


hostname = 'rethinkdb.galahad.com'
rethinkdb_cert = '/var/private/ssl/rethinkdb_cert.pem'

if not os.path.isfile(rethinkdb_cert):

    print('File not found:', rethinkdb_cert)
    sys.exit(1)

conn = r.connect(
    host=hostname,
    port=28015,
    ssl={'ca_certs': rethinkdb_cert}).repl()

# setup database and tables
try:
    r.db_create('transducers').run(conn)
except r.ReqlOpFailedError:
    # database already exists - great
    pass

try:
    r.db('transducers').table_create('commands').run(conn)
except r.ReqlOpFailedError:
    # table already exists - great
    pass

try:
    r.db('transducers').table_create('acks').run(conn)
except r.ReqlOpFailedError:
    # table already exists - great
    pass

try:
    r.db('transducers').table_create('galahad').run(conn)
except r.ReqlOpFailedError:
    # table already exists - great
    pass


excalibur_private_key = '/var/private/ssl/excalibur_private_key.pem'

if not os.path.isfile(excalibur_private_key):

    print('File not found:', excalibur_private_key)
    sys.exit(1)

# create users
r.db('rethinkdb').table('users').insert({
    'id': 'excalibur',
    'password': {
        'password': open(excalibur_private_key).read(),
        'iterations': 4096
    }}).run(conn)
r.db('rethinkdb').table('users').insert({
    'id': 'virtue',
    'password': {
        'password': 'virtue',
        'iterations': 4096
    }}).run(conn)

# set permissions for users
r.grant('excalibur', {'config': True}).run(conn)
r.db('transducers').table('commands').grant('excalibur', {'read': True, 'write': True}).run(conn)
r.db('transducers').table('acks').grant('excalibur', {'read': True, 'write': False}).run(conn)

r.db('transducers').table('commands').grant('virtue', {'read': True, 'write': False}).run(conn)
r.db('transducers').table('acks').grant('virtue', {'read': True, 'write': True}).run(conn)

print('Finished')
