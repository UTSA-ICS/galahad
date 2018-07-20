#!/usr/bin/python
import time
import rethinkdb as r
r.connect("172.30.93.138",28015).repl()

while True:
	r.db('routing').table('transducer').filter(r.row['transducerId']=='m1').update({'flag':'TRUE'}).run()
	r.db('routing').table('transducer').filter(r.row['transducerId']=='m1').run()
	time.sleep(90)
