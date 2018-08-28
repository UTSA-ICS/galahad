import rethinkdb as r
import socket
r.connect("172.30.1.54",28015).repl()
ip = socket.gethostbyname(socket.gethostname())

with open('me.cfg', 'a') as config:
        cursor = r.db('routing').table('galahad').filter((r.row["address"]==ip) & (r.row["function"]=="compute")).run()
        addr = cursor.next()['guestnet']
	config.write(addr)

with open('virtue-galahad.cfg', 'a') as config:
        cursor = r.db('routing').table('galahad').filter(r.row["function"]=="router").run()
	addr=cursor.next()['address']
	config.write(addr+'\n')

with open('domus.cfg', 'a') as config:
	cursor = r.db('routing').table('galahad').filter((r.row["function"]=="router") & (r.row["address"]==ip)).run()
