#!/usr/bin/env python

###
#  For debugging only - prints contents of database
###

import rethinkdb as r

# Change path to ca cert as necessary
conn = r.connect(user='virtue', password='virtue', ssl={'ca_certs': 'rethinkdb_cert.pem'})

print 'COMMANDS:'
for x in r.db('transducers').table('commands').run(conn):
   print x['virtue_id'], x['transducer_id'], x['enabled'], x['timestamp']

print ''
print 'ACKS:'
for x in r.db('transducers').table('acks').run(conn):
   print x['virtue_id'], x['transducer_id'], x['enabled'], x['timestamp']

