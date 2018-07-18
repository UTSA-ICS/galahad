#!/usr/bin/python
import rethinkdb as r
r.connect("172.30.93.138",28015).repl()

print r.db('routing').table('galahad').filter(r.row['host']=='test').delete().run()
print r.db('routing').table('galahad').run()
