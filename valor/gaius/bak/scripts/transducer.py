#!/usr/bin/python
import rethinkdb as r
r.connect("172.30.93.138",28015).repl()

#flags a transducer object for migration
r.db('routing').table('transducer').filter(r.row['transducerId']=='m1').update({'flag':'TRUE'}).run()
r.db('routing').table('transducer').filter(r.row['transducerId']=='m1').run()
