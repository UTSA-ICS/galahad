#!/usr/bin/python
import rethinkdb as r
import sys
import subprocess

r.connect("172.30.93.138",28015).repl()

print "ALERT TEST"
r.db('routing').table('transducer').filter(r.row['transducerId']=='m1').update({'flag':'FALSE'}).run()
r.db('routing').table('transducer').filter(r.row['transducerId']=='m1').run()
print subprocess.Popen("rm ./config/" + sys.argv[1] + ".cfg", shell=True, stdout=subprocess.PIPE).stdout.read()
