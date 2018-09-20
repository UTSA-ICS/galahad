#!/usr/bin/python
import rethinkdb as r

r.connect(
    '172.30.1.54',
    28015,
    ssl = {
        'ca_certs': '/home/ubuntu/rethinkdb_cert.pem'
    }).repl()

print r.db('transducers').table('galahad').filter(r.row['host']=='centos-test').delete().run()
print r.db('transducers').table('galahad').run()
