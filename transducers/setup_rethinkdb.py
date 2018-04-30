# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

import rethinkdb as r

# connect
conn = r.connect(\
	host='ec2-54-145-211-31.compute-1.amazonaws.com',\
	ssl={'ca_certs': 'rethinkdb_cert.pem'})

# setup database and tables
try:
	r.db_create('transducers').run(conn)
except r.ReqlOpFailedError:
	# database already exists - great
	pass

try:
	r.db('transducers').table_create('commands').run(conn)
except r.ReqlOpFailedError:
	# table already exists - great
	pass

try:
	r.db('transducers').table_create('acks').run(conn)
except r.ReqlOpFailedError:
	# table already exists - great
	pass

# key filename (for password)
excalibur_private_key = 'excalibur_key.pem'

# create users
r.db('rethinkdb').table('users').insert({
	'id': 'excalibur', 
	'password': {
		'password': open(excalibur_private_key).read(), 
		'iterations': 4096
}}).run(conn)
r.db('rethinkdb').table('users').insert({
	'id': 'virtue', 
	'password': {
		'password': 'virtue', 
		'iterations': 4096
}}).run(conn)

# set permissions for users
r.grant('excalibur', {'config': True}).run(conn)
r.db('transducers').table('commands').grant('excalibur', {'read':True, 'write':True}).run(conn)
r.db('transducers').table('acks').grant('excalibur', {'read':True, 'write':False}).run(conn)

r.db('transducers').table('commands').grant('virtue', {'read':True, 'write':False}).run(conn)
r.db('transducers').table('acks').grant('virtue', {'read':True, 'write':True}).run(conn)

