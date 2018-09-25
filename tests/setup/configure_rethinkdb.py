#!/usr/bin/env python

# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

import argparse
import os.path
import rethinkdb as r
import sys

parser = argparse.ArgumentParser(description='Set up script for RethinkDB for transducer control')
parser.add_argument('-r', '--host', help='Hostname of RethinkDB', default='rethinkdb.galahad.com')
parser.add_argument('-c', '--cert', help='Path to RethinkDB CA cert', default='/var/private/ssl/rethinkdb_cert.pem')
parser.add_argument('-e', '--excalkey', help='Private key for Excalibur', default='/var/private/ssl/excalibur_key.pem')

args = parser.parse_args()

if not os.path.isfile(args.cert):
	print 'File not found:', args.cert
	sys.exit(1)
if not os.path.isfile(args.excalkey):
	print 'File not found:', args.excalkey
	sys.exit(1)

conn = r.connect(host=args.host, ssl={'ca_certs': args.cert})

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

try:
	r.db('transducers').table_create('galahad').run(conn)
except r.ReqlOpFailedError:
	# table already exists - great
	pass

r.db('transducers').table('galahad').insert([
	{ "host" 	: "i-04d0aaf3c6c86572f",
	  "function" 	: "router",
	  "address"	: "172.30.1.53",
	  "guestnet"	: "10.91.0.254" }]).run()
r.db('transducers').table('galahad').insert([
	{ "host"	: "i-0416d64601be1edbd",
	  "function"	: "compute",
	  "address"	: "172.30.1.51",
	  "guestnet"	: "10.91.0.1" }]).run()
r.db('transducers').table('galahad').insert([
	{ "host"	: "i-0a95cbd2d8f37c8a7",
	  "function"	: "compute",
	  "address"	: "172.30.1.52",
	  "guestnet"	: "10.91.0.2" }]).run()

# key filename (for password)
excalibur_private_key = args.excalkey

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

print 'Finished'
