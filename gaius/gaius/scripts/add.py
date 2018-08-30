#!/usr/bin/python
import rethinkdb as r
r.connect("172.30.1.54",28015).repl()

r.db('routing').table('galahad').insert([{
	'function':'virtue',
	'host':'centos-test',
	'address':'172.30.87.98',
	'guestnet':'10.91.0.5'}]).run()
