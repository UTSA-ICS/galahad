#!/usr/bin/env python2

###############################################################################
#
# MERLIN: Mediator of Events for Responses, Logging, and IntrospectioN
#
###############################################################################

import argparse
import json
import logging
import rethinkdb as r
import os
import signal
import sys
import socket
import traceback
from copy import deepcopy
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from struct import pack
from threading import Thread, Lock, Event
from time import sleep, time

log = logging.getLogger('merlin')

def setup_logging(filename):
	logfile = logging.FileHandler(filename)
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	logfile.setFormatter(formatter)
	log.addHandler(logfile)
	log.setLevel(logging.INFO)

# Signal handler to be able to Ctrl-C even if we're in the heartbeat
def signal_handler(signal, frame):
	exit.set()
	sys.exit(0)

# Generate a signature for a given message
def sign_message(virtue_id, transducer_id, config, enabled, timestamp, virtue_key):
	message = '|'.join([virtue_id, transducer_id, str(config), str(enabled), str(timestamp)])
	h = SHA.new(str(message))
	signer = PKCS1_v1_5.new(virtue_key)
	signature = signer.sign(h)
	return signature

# Verify a signature for a given message
def verify_message(virtue_id, transducer_id, config, enabled, timestamp, signature, excalibur_key):
	message = '|'.join([virtue_id, transducer_id, str(config), str(enabled), str(timestamp)])
	h = SHA.new(str(message))
	verifier = PKCS1_v1_5.new(excalibur_key)
	return verifier.verify(h, signature)

# Connect to a unix domain socket
def connect_socket(path):
	sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	try:
		sock.connect(path)
	except socket.error, msg:
		log.error('Failed to connect to socket: %s', msg)
		return None
	return sock

# Send given message over a unix domain socket
def send_message(sock, message):
	try:
		# Send length of upcoming message
		sock.sendall(pack('!i', len(message)))
		# Send actual message
		sock.sendall(message)
		return True
	except socket.error, msg:
		log.error('Failed to send message: %s', msg)
		return False

# Receive message over a unix domain socket
def receive_message(sock):
	all_data = ''
	try:
		while True:
			data = sock.recv(256)
			if data:
				all_data += data
			else:
				break
	except socket.error, msg:
		log.error('Failed while receiving message: %s', msg)
		return None
	finally:
		log.info('Received data: %s', all_data)
		sock.close()
	return all_data

def repopulate_ruleset(virtue_id, heartbeat_conn, socket_to_filter, virtue_key):
	# Get latest ruleset from the ACK table
	rows = r.db('transducers').table('acks')\
		.filter({ 'virtue_id': virtue_id })\
		.run(heartbeat_conn)

	ruleset = {}
	for row in rows:
		# Check keys and retrieve values
		required_keys = ['virtue_id', 'transducer_id', 'configuration', 
			'enabled', 'timestamp', 'signature']
		if not all( [ (key in row) for key in required_keys ] ):
			log.error('Missing required keys in row: %s',\
				str(filter((lambda key: key not in row), required_keys)))
			continue
		transducer_id = row['transducer_id']
		config = row['configuration']
		enabled = row['enabled']
		timestamp = row['timestamp']
		signature = row['signature']

		# Validate message's signature
		printable_msg = deepcopy(row)
		del printable_msg['signature']
		new_signature = sign_message(virtue_id, transducer_id, config, enabled, timestamp, virtue_key)
		if new_signature == signature:
			log.info('Retrieved valid ACK: %s', \
				json.dumps(printable_msg, indent=2))
			ruleset[transducer_id] = enabled
		else:
			log.error('Retrieved invalid ACK: %s', \
				json.dumps(printable_msg, indent=2))
			continue

	if len(ruleset) > 0:
		# Inform filter of changes through unix domain socket
		sock = connect_socket(socket_to_filter)
		if sock is None:
			log.error('Unable to connect to socket')
			return

		if not send_message(sock, json.dumps(ruleset)):
			log.error('Failed to send ruleset to filter')
			return

		all_data = receive_message(sock)
		if all_data is None:
			log.error('Failed to receive response from filter')
			return
	log.info('Successfully reminded filter of ruleset')

def process_update(virtue_id, heartbeat_conn, current_ruleset):
	transducers = []
	timestamp = int(time())
	for transducer_id in current_ruleset:
		enabled = current_ruleset[transducer_id]
		# TODO: We don't care about the config right now but eventually we should
		#config = current_ruleset[transducer_id]
		config = '{}'
		row_signature = sign_message(virtue_id, transducer_id, config, enabled, timestamp, virtue_key)
		transducers.append({
			'id': [virtue_id, transducer_id],
			'virtue_id': virtue_id,
			'transducer_id': transducer_id,
			'configuration': config,
			'enabled': enabled,
			'timestamp': timestamp,
			'signature': r.binary(row_signature)
		})
	try:
		res = r.db('transducers').table('acks')\
			.insert(transducers, conflict='replace')\
			.run(heartbeat_conn, durability='soft')
		if res['errors'] > 0:
			log.error('Failed to insert into ACKs table; first error: %s', str(res['first_error']))
	except r.ReqlError as e:
		log.error('Failed to insert into ACKs table because: %s', str(e))

# Perform a heartbeat - get the current ruleset from the filter periodically
def heartbeat(virtue_id, rethinkdb_host, ca_cert, interval_len, virtue_key, path_to_socket):
	# Rethinkdb connection
	heartbeat_conn = None
	while heartbeat_conn is None:
		try:
			heartbeat_conn = r.connect(host=rethinkdb_host, 
						user='virtue', 
						password='virtue', 
						ssl={ 'ca_certs': ca_cert })
		except r.ReqlDriverError as e:
			log.error('Failed to connect to RethinkDB at host: %s; error: %s', rethinkdb_host, str(e))
			sleep(30)

	while not exit.is_set():
		# Lock so that we don't interrupt a real command
		with lock:
			# (New function so return can be used on error conditions)
			def do_heartbeat():
				sock = connect_socket(path_to_socket)
				if sock is None:
					log.error('Failed to connect to socket')
					return

				# Request a heartbeat from the syslog-ng filter
				if not send_message(sock, 'heartbeat'):
					log.error('Failed to request heartbeat')
					return

				log.info('Heartbeat')

				data = receive_message(sock)
				if data is None:
					log.error('Failed to receive response to heartbeat')
					return

				current_ruleset = json.loads(data)

				# If the filter restarted and lost its ruleset, repopulate it
				if len(current_ruleset) == 0:
					repopulate_ruleset(virtue_id, heartbeat_conn, socket_to_filter, virtue_key)
				else:
					process_update(virtue_id, heartbeat_conn, current_ruleset)
			do_heartbeat()

		# Wait until the next heartbeat
		# Do not call this inside `with lock` above!!!
		exit.wait(interval_len)

def listen_for_commands(virtue_id, excalibur_key, virtue_key, rethinkdb_host, socket_to_filter):
	conn = None
	while conn is None:
		try:
			conn = r.connect(host=rethinkdb_host, 
				user='virtue', 
				password='virtue', 
				ssl={ 'ca_certs': args.ca_cert })
		except r.ReqlDriverError as e:
			log.error('Failed to connect to RethinkDB at host: %s; error: %s', rethinkdb_host, str(e))
			sleep(30)

	log.info('Waiting for ruleset change commands for Virtue: %s', virtue_id)

	# Listen for changes (receive commands through rethinkdb)
	for change in r.db('transducers').table('commands')\
		.filter( r.row['virtue_id'].eq(virtue_id) )\
		.changes().run(conn):

		row = change['new_val']

		# Check keys and retrieve values
		required_keys = ['virtue_id', 'transducer_id', 'configuration', 
                        'enabled', 'timestamp', 'signature']
		if not all( [ (key in row) for key in required_keys ] ):
                        log.error('Missing required keys in row: %s',\
                                str(filter((lambda key: key not in row),required_keys)))
			continue
		transducer_id = row['transducer_id']
		config = row['configuration']
		enabled = row['enabled']
		timestamp = row['timestamp']
		signature = row['signature']

		# Validate message's signature
		printable_msg = deepcopy(row)
		del printable_msg['signature']
		if verify_message(virtue_id, transducer_id, config, enabled, timestamp, signature, excalibur_key):
			log.info('Received valid command message: %s', \
				json.dumps(printable_msg, indent=2))
		else:
			log.error('Unable to validate signature of command message: %s', \
				json.dumps(printable_msg, indent=2))
			continue

		with lock:
			log.info('Begin implementing received command')

			# Inform filter of changes through unix domain socket
			sock = connect_socket(socket_to_filter)
			if sock is None:
				log.error('Unable to connect to socket')
				continue

			command = { transducer_id : enabled }
			if not send_message(sock, json.dumps(command)):
				log.error('Failed to send command to filter')
				continue

			all_data = receive_message(sock)
			if all_data is None:
				log.error('Failed to receive response from filter')
				continue

			# Confirm to excalibur that changes were successful
			new_signature = sign_message(virtue_id, transducer_id, config, enabled, timestamp, virtue_key)

			try:
				res = r.db('transducers').table('acks').insert({
					'id': [virtue_id, transducer_id],
					'virtue_id': virtue_id,
					'transducer_id': transducer_id,
					'configuration': config,
					'enabled': enabled,
					'timestamp': timestamp,
					'signature': r.binary(new_signature)
				}, conflict='replace').run(conn)
				if res['errors'] > 0:
					log.error('Failed to insert into ACKs table; first error: %s', str(res['first_error']))
					continue
			except r.ReqlError as e:
				log.error('Failed to publish ACK to Excalibur because: %s', str(e))
				continue

			log.info('Successfully implemented command from Excalibur')

if __name__ == '__main__':
	exit = Event()
	signal.signal(signal.SIGINT, signal_handler)

	parser = argparse.ArgumentParser(description='Receiver for Virtue transducer ruleset changes')
	parser.add_argument('virtue_id', help='ID of this Virtue')
	parser.add_argument('-r', '--rdb_host', help='RethinkDB host', default='rethinkdb.galahad.com')
	parser.add_argument('-c', '--ca_cert', help='RethinkDB CA cert', default='rethinkdb_cert.pem')
	parser.add_argument('-e', '--excalibur_key', help='Public key file for Excalibur', default='excalibur_pub.pem')
	parser.add_argument('-v', '--virtue_key', help='Private key file for this Virtue', default='virtue_key.pem')
	parser.add_argument('-i', '--heartbeat', help='Heartbeat interval (sec)', type=int, default=30)
	parser.add_argument('-s', '--socket', help='Path to socket to filter', default='/opt/merlin/receiver_to_filter')
	parser.add_argument('-l', '--log', help='Path to log file', default='merlin.log')
	args = parser.parse_args()

	setup_logging(args.log)

	if not os.path.isfile(args.ca_cert):
		log.error('CA cert file does not exist: %s', args.ca_cert)
		sys.exit(1)
	if not os.path.isfile(args.excalibur_key):
		log.error('Excalibur public key file does not exist: %s', args.excalibur_key)
		sys.exit(1)
	if not os.path.isfile(args.virtue_key):
		log.error('Virtue private key file does not exist: %s', args.virtue_key)
		sys.exit(1)
	if args.heartbeat < 0:
		log.error('Invalid heartbeat interval: %d', args.heartbeat)
		sys.exit(1)

	# Load keys into memory
	virtue_key = None
	with open(args.virtue_key, 'r') as f:
		virtue_key = RSA.importKey(f.read())

	excalibur_key = None
	with open(args.excalibur_key, 'r') as f:
		excalibur_key = RSA.importKey(f.read())

	lock = Lock()

	# TODO: set up initial ruleset, as well as actions on restart

	heartbeat_thread = Thread(target = heartbeat, args=(
		args.virtue_id, args.rdb_host, args.ca_cert, args.heartbeat, 
		virtue_key, args.socket,))
	heartbeat_thread.start()

	listen_for_commands(args.virtue_id, excalibur_key, virtue_key, args.rdb_host, socket_to_filter)

