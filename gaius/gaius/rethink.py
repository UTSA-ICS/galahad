#!/usr/bin/python
import rethinkdb as r
import socket

class Rethink():
    r.connect("172.30.1.54",28015).repl()
    ip = socket.gethostbyname(socket.gethostname())

    def filter(self, table, filt):
        return r.db('routing').table(table).filter(filt).run()

    def update(self, table, filt, vals):
        try:
            r.db('routing').table(table).filter(filt).update(vals).run()
        except:
            print('Error updating table')

    def insert(self, table, vals):
        try:
            r.db('routing').table(table).insert(vals).run()
        except:
            print('Error inserting values')

    def delete(self, table, filt):
        try:
            r.db('routing').table(table).filter(filt).delete().run()
        except:
            print('Error deleting values')

    def get_guestnet(self):
        highest = r.db('routing').table('galahad').filter(lambda doc: (doc['function'] == 'virtue') \
            or (doc['function'] == 'valor')).order_by(r.desc('guestnet')).limit(1).run()
        old = highest[0]['guestnet']
        new = int(old.rpartition('.')[-1]) + 1
        final = old.rpartition('.')[0] + '.' + str(new)
        return final

