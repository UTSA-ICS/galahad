#!/usr/bin/env python2

###############################################################################
#
# MERLIN: Mediator of Events for Responses, Logging, and IntrospectioN
#
###############################################################################

import argparse
import json
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
		print 'ERROR: Failed to connect to socket:', msg
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
		print 'ERROR: Failed to send message:', msg
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
		print 'ERROR: Failed while receiving message:', msg
		return None
	finally:
		print 'INFO: Received data:', all_data
		sock.close()
	return all_data

# Perform a heartbeat - get the current ruleset from the filter periodically
def heartbeat(virtue_id, rethinkdb_host, ca_cert, interval_len, virtue_key, path_to_socket):
	# Rethinkdb connection
	try:
		heartbeat_conn = r.connect(host=rethinkdb_host, 
					user='virtue', 
					password='virtue', 
					ssl={ 'ca_certs': ca_cert })
	except ReqlDriverError as e:
		print 'ERROR: Failed to connect to RethinkDB at host:', rethinkdb_host, 'error:', e
		return

	while not exit.is_set():
		# Lock so that we don't interrupt a real command
		with lock:
			sock = connect_socket(path_to_socket)
			if sock is None:
				print 'ERROR: Failed to connect to socket'
				exit.wait(interval_len)
				continue

			# Request a heartbeat from the syslog-ng filter
			if not send_message(sock, 'heartbeat'):
				print 'ERROR: Failed to request heartbeat'
				exit.wait(interval_len)
				continue
			print 'Heartbeat'

			data = receive_message(sock)
			if data is None:
				print 'ERROR: Failed to receive response to heartbeat'
				exit.wait(interval_len)
				continue
			current_ruleset = json.loads(data)

			# If the filter restarted and lost its ruleset, repopulate it
			if len(current_ruleset) == 0:
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
						print 'ERROR: Missing required keys in row:',\
							filter((lambda key: key not in row),required_keys)
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
						print 'INFO: Retrieved valid ACK:', \
							json.dumps(printable_msg, indent=2)
						ruleset[transducer_id] = enabled
					else:
						print 'ERROR: Retrieved invalid ACK:', \
							json.dumps(printable_msg, indent=2)
						continue

				if len(ruleset) > 0:
					# Inform filter of changes through unix domain socket
					sock = connect_socket(socket_to_filter)
					if sock is None:
						print 'ERROR: Unable to connect to socket'
						continue

					if not send_message(sock, json.dumps(ruleset)):
						print 'ERROR: Failed to send ruleset to filter'
						continue

					all_data = receive_message(sock)
					if all_data is None:
						print 'ERROR: Failed to receive response from filter'
						continue
				print 'INFO: Successfully reminded filter of ruleset'

				continue

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
					print 'ERROR: Failed to insert into ACKs table; first error:'
					print res['first_error']
			except r.ReqlError as e:
				print 'ERROR: Failed to insert into ACKs table because:', e

		# Wait until the next heartbeat
		exit.wait(interval_len)

def listen_for_commands(virtue_id, excalibur_key, virtue_key, rethinkdb_host, socket_to_filter):
	try:
		conn = r.connect(host=rethinkdb_host, 
			user='virtue', 
			password='virtue', 
			ssl={ 'ca_certs': args.ca_cert })
	except ReqlDriverError as e:
		print 'ERROR: Failed to connect to RethinkDB at host:', rethinkdb_host, 'error:', e

	print 'INFO: Waiting for ruleset change commands for Virtue:', virtue_id

	# Listen for changes (receive commands through rethinkdb)
	for change in r.db('transducers').table('commands')\
		.filter( r.row['virtue_id'].eq(virtue_id) )\
		.changes().run(conn):

		row = change['new_val']

		# Check keys and retrieve values
		required_keys = ['virtue_id', 'transducer_id', 'configuration', 
                        'enabled', 'timestamp', 'signature']
		if not all( [ (key in row) for key in required_keys ] ):
                        print 'ERROR: Missing required keys in row:',\
                                filter((lambda key: key not in row),required_keys)
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
			print 'INFO: Received valid command message:', \
				json.dumps(printable_msg, indent=2)
		else:
			print 'ERROR: Unable to validate signature of command message:', \
				json.dumps(printable_msg, indent=2)
			continue

		with lock:
			print 'INFO: Begin implementing received command'

			# Inform filter of changes through unix domain socket
			sock = connect_socket(socket_to_filter)
			if sock is None:
				print 'ERROR: Unable to connect to socket'
				continue

			command = { transducer_id : enabled }
			if not send_message(sock, json.dumps(command)):
				print 'ERROR: Failed to send command to filter'
				continue

			all_data = receive_message(sock)
			if all_data is None:
				print 'ERROR: Failed to receive response from filter'
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
					print 'ERROR: Failed to insert into ACKs table; first error:'
					print res['first_error']
					continue
			except r.ReqlError as e:
				print 'ERROR: Failed to publish ACK to Excalibur because:', e
				continue

			print 'INFO: Successfully implemented command from Excalibur'

if __name__ == '__main__':
	exit = Event()
	signal.signal(signal.SIGINT, signal_handler)

	parser = argparse.ArgumentParser(description='Receiver for Virtue transducer ruleset changes')
	parser.add_argument('virtue_id', help='ID of this Virtue')
	parser.add_argument('-r', '--rdb_host', help='RethinkDB host', default='ec2-54-145-211-31.compute-1.amazonaws.com')
	parser.add_argument('-c', '--ca_cert', help='RethinkDB CA cert', default='rethinkdb_cert.pem')
	parser.add_argument('-e', '--excalibur_key', help='Public key file for Excalibur', default='excalibur_pub.pem')
	parser.add_argument('-v', '--virtue_key', help='Private key file for this Virtue', default='virtue_key.pem')
	parser.add_argument('-i', '--heartbeat', help='Heartbeat interval (sec)', type=int, default=30)
	args = parser.parse_args()

	if not os.path.isfile(args.ca_cert):
		print 'ERROR: CA cert file does not exist:', args.ca_cert
		sys.exit(1)
	if not os.path.isfile(args.excalibur_key):
		print 'ERROR: Excalibur public key file does not exist:', args.excalibur_key
		sys.exit(1)
	if not os.path.isfile(args.virtue_key):
		print 'ERROR: Virtue private key file does not exist:', args.virtue_key
		sys.exit(1)
	if args.heartbeat < 0:
		print 'ERROR: Invalid heartbeat interval:', args.heartbeat
		sys.exit(1)

	socket_to_filter = '/opt/receiver_to_filter'

	# Load keys into memory
	virtue_key = None
	with open(args.virtue_key, 'r') as f:
		virtue_key = RSA.importKey(f.read())

	excalibur_key = None
	with open(args.excalibur_key, 'r') as f:
		excalibur_key = RSA.importKey( f.read() )

	lock = Lock()

	# TODO: set up initial ruleset, as well as actions on restart

	heartbeat_thread = Thread(target = heartbeat, args=(
		args.virtue_id, args.rdb_host, args.ca_cert, args.heartbeat, 
		virtue_key, socket_to_filter,))
	heartbeat_thread.start()

	listen_for_commands(args.virtue_id, excalibur_key, virtue_key, args.rdb_host, socket_to_filter)

