#!/usr/bin/python
import rethinkdb as r
import socket

class Rethink():
	r.connect("172.30.93.138",28015).repl()
	ip = socket.gethostbyname(socket.gethostname())

	#filter for an onject in the routing database
	def filter(self, table, filt):
		return r.db('routing').table(table).filter(filt).run()

	#updates an object in the routing database
	def update(self, table, filt, vals):
		try:
			r.db('routing').table(table).filter(filt).update(vals).run()
		except:
			print 'Error updating table'

	#inserts an object into the routing database
	def insert(self, table, vals):
		try:
			r.db('routing').table(table).insert(vals).run()
		except:
			print 'Error inserting values'

	#removes an object from the routing database
	def delete(self, table, filt):
		try:
			r.db('routing').table(table).filter(filt).delete().run()
		except:
			print 'Error deleting values'

	#takes the next highest guestnet of an object in the galahad database to use for new objects
	def get_guestnet(self):
		highest = r.db('routing').table('galahad').filter(lambda doc: (doc['function'] == 'virtue') \
			or (doc['function'] == 'valor')).order_by(r.desc('guestnet')).limit(1).run()
		old = highest[0]['guestnet']
		new = int(old.rpartition('.')[-1]) + 1
		final = old.rpartition('.')[0] + '.' + str(new)
		return final

