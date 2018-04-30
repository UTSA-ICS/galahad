# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

import rethinkdb as r

pw = raw_input('Set rethinkdb admin password to: ').strip()

conn = r.connect(\
	host='ec2-54-145-211-31.compute-1.amazonaws.com',\
	ssl={'ca_certs': 'rethinkdb_cert.pem'})
r.db('rethinkdb').table('users').update({
	'id': 'admin', 
	'password': {
		'password': pw, 
		'iterations': 4096
	}
}).run(conn)

print 'Finished'
