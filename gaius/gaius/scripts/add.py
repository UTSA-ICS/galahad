#!/usr/bin/python
import rethinkdb as r
r.connect("172.30.93.138",28015).repl()

#adds an instance to the table
r.db('routing').table('galahad').insert([{
	'function':'virtue',
	'host':'test',
	'address':'172.30.87.100',
	'guestnet':'10.91.0.1'}]).run()
