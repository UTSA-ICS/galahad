#!/usr/bin/env python

# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

import argparse
import os.path
import rethinkdb as r
import sys

parser = argparse.ArgumentParser(description='Script to set admin password for RethinkDB')
parser.add_argument('-h', '--host', help='Hostname of RethinkDB', default='rethinkdb.galahad.lab')
parser.add_argument('-c', '--cert', help='Path to RethinkDB CA cert', default='/var/private/ssl/rethinkdb_cert.pem')

args = parser.parse_args()

if not os.path.isfile(args.cert):
	print 'File not found:', args.cert
	sys.exit(1)

conn = r.connect(host=args.host, ssl={'ca_certs': args.cert})

pw = raw_input('Set rethinkdb admin password to: ').strip()

r.db('rethinkdb').table('users').update({
	'id': 'admin', 
	'password': {
		'password': pw, 
		'iterations': 4096
	}
}).run(conn)

print 'Finished'
