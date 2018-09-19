import rethinkdb as r
import socket
r.connect("172.30.1.45",28015).repl()
ip = socket.gethostbyname(socket.gethostname())


with open('me.cfg', 'a') as config:
        ip = socket.gethostbyname(socket.gethostname())
        cursor = r.db('routing').table('galahad').filter(r.row["address"]==ip).run()
        addr = cursor.next()['guestnet']
	config.write(addr)

with open('virtue-galahad.cfg', 'a') as config:
        cursor = r.db('routing').table('galahad').filter(r.row["function"]=="compute").run()
        for document in cursor:
                config.write(document['address']+"\n")
