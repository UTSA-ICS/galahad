#!/usr/bin/python
import rethinkdb as r
r.connect('rethinkdb.galahad.com', 28015).repl()

print r.db('routing').table('transducer').filter(r.row['transducerId']=='m1').update({'flag':'TRUE'}).run()
print r.db('routing').table('transducer').filter(r.row['transducerId']=='m1').run()
print r.db('routing').table('transducer').filter(r.row['transducerId']=='m1').update({'flag':'FALSE'}).run()
print r.db('routing').table('transducer').filter(r.row['transducerId']=='m1').run()
