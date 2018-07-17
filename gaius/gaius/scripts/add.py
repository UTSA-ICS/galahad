#!/usr/bin/python
import rethinkdb as r
r.connect("172.30.93.138",28015).repl()

r.db('routing').table('galahad').insert([{
	'function':'x',
	'host':'nx.tx',
	'address':'172.30.87.x',
	'guestnet':'10.91.0.x'}]).run()
