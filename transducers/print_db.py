#!/usr/bin/env python

###
#  For debugging only - prints contents of database
###

import rethinkdb as r
import json

# Change path to ca cert as necessary
conn = r.connect(host='rethinkdb.galahad.com',
                 # user='virtue',
                 # password='virtue',
                 ssl={'ca_certs': 'galahad-config/rethinkdb_keys/rethinkdb_cert.pem'})

print("COMMANDS:")
for x in r.db('transducers').table('commands').run(conn):
    if 'signature' in x:
        del x['signature']
    print(json.dumps(x, indent=2))

print("")
print("ACKS:")
for x in r.db('transducers').table('acks').run(conn):
    if 'signature' in x:
        del x['signature']
    print(json.dumps(x, indent=2))

print("")
print("GALAHAD:")
for x in r.db('transducers').table('galahad').run(conn):
    print(json.dumps(x, indent=2))
