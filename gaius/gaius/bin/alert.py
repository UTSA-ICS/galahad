#!/usr/bin/python
import rethinkdb as r
import sys
import subprocess

r.connect("172.30.93.138",28015).repl()

r.db('routing').table('transducer').filter(r.row['transducerId']=='m1').update({'flag':'FALSE'}).run()
r.db('routing').table('transducer').filter(r.row['transducerId']=='m1').run()
