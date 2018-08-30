#!/usr/bin/python
import rethinkdb as r
r.connect("172.30.1.54",28015).repl()

print r.db('routing').table('galahad').filter(r.row['host']=='centos-test').delete().run()
print r.db('routing').table('galahad').run()
