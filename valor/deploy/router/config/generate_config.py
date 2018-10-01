import rethinkdb as r
import socket

r.connect(
    "rethinkdb.galahad.com",
    28015,
    ssl={
        'ca_certs': '/var/private/ssl/rethinkdb_cert.pem'
    }).repl()

ip = socket.gethostbyname(socket.gethostname())

with open('me.cfg', 'a') as config:
    cursor = r.db('transducers').table('galahad').filter(r.row["address"] == ip).run()
    addr = cursor.next()['guestnet']
    config.write(addr)

with open('virtue-galahad.cfg', 'a') as config:
    cursor = r.db('transducers').table('galahad').filter(r.row["function"] == "valor").run()
    for document in cursor:
        config.write(document['address'] + "\n")
