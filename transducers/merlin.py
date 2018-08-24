#!/usr/bin/env python2

###############################################################################
#
# MERLIN: Mediator of Events for Responses, Logging, and IntrospectioN
# Copyright (c) 2018 by Raytheon BBN Technologies Corp.
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
import subprocess
import traceback
import re
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
def sign_message(virtue_id, transducer_id, transducer_type, config, enabled, timestamp, virtue_key):
	message = '|'.join([virtue_id, transducer_id, transducer_type, str(config), str(enabled), str(timestamp)])
	h = SHA.new(str(message))
	signer = PKCS1_v1_5.new(virtue_key)
	signature = signer.sign(h)
	return signature

# Verify a signature for a given message
def verify_message(virtue_id, transducer_id, transducer_type, config, enabled, timestamp, signature, excalibur_key):
	message = '|'.join([virtue_id, transducer_id, transducer_type, str(config), str(enabled), str(timestamp)])
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

# Connect to a netlink socket
def connect_socket_netlink():
	sock = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, 31)
	try:
		# pid 0 is kernel
		sock.connect((0, 0))
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

# Send given message over a netlink socket
def send_message_netlink(sock, array):
	tosend = ''
	try:
		# Send length of array
		message = pack('=i', len(array))
		for msg in array:
			if type(msg) is not str and type(msg) is not unicode:
				log.error('Invalid array element type: %s', str(type(msg)))
				continue
			# Send length of each element, then the string itself
			message += pack('=i', len(msg))
			message += msg
			message += '\0'

		# This is a netlink header:
		# 32 bits: length of message including header
		# 16 bits: message content type
		# 16 bits: additional flags
		# 32 bits: sequence number (doesn't seem to be actually used?)
		# 32 bits: sending process PID
		hdrlen = 4 * 3 + 2 * 2  # 3 ints, 2 shorts
		hdr = pack('=LHHLL', hdrlen + len(message), 0, 0, 0, os.getpid())

		tosend = str(hdr) + str(message) + '\r\n'
	except Exception as e:
		log.error('Error constructing netlink message: ' + str(e))
		return False

	try:
		sock.sendall(tosend)
		return True
	except socket.error, msg:
		log.error('Failed to send netlink message: %s', msg)
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
		required_keys = ['virtue_id', 'transducer_id', 'type', 'configuration', 
			'enabled', 'timestamp', 'signature']
		if not all( [ (key in row) for key in required_keys ] ):
			log.error('Missing required keys in row: %s',\
				str(filter((lambda key: key not in row), required_keys)))
			continue
		transducer_id = row['transducer_id']
		transducer_type = row['type']
		config = row['configuration']
		enabled = row['enabled']
		timestamp = row['timestamp']
		signature = row['signature']

		# Validate message's signature
		printable_msg = deepcopy(row)
		del printable_msg['signature']
		new_signature = sign_message(virtue_id, transducer_id, transducer_type, config, enabled, timestamp, virtue_key)
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
		transducer_type = 'SENSOR'
		row_signature = sign_message(virtue_id, transducer_id, transducer_type, config, enabled, timestamp, virtue_key)
		transducers.append({
			'id': [virtue_id, transducer_id],
			'virtue_id': virtue_id,
			'transducer_id': transducer_id,
			'type': transducer_type,
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
					repopulate_ruleset(virtue_id, heartbeat_conn, path_to_socket, virtue_key)
				else:
					process_update(virtue_id, heartbeat_conn, current_ruleset)
			do_heartbeat()

		# Wait until the next heartbeat
		# Do not call this inside `with lock` above!!!
		exit.wait(interval_len)


def do_actuator(transducer_id, config_str, enabled):

	try:
		config = json.loads(config_str)
	except (ValueError, TypeError), e:
		if enabled == True:
			log.error('Failed to parse config str as json: ' + str(e) + '; config: ' + str(config_str))
			return False

	if transducer_id == 'kill_proc':
		# Actuator that both immediately kills a process (by name) and also prevents it from ever starting again (until actuator rule is disabled/removed)
                if not enabled:
                        config = { 'processes': [] }

		if 'processes' not in config or \
			type(config['processes']) is not list or \
			any(type(e) is not str and type(e) is not unicode for e in config['processes']):

			log.error('The actuator kill_process MUST contain a "processes" key in its configuration that corresponds to a list of strings')
			return False

		processes = config['processes']
		success = True

		for p in processes:
			# Send name of process that should be immediately killed to the processkiller service (running as root) that is listening on this socket
			proc_kill_sock_path = '/var/run/deathnote'
			proc_kill_sock = connect_socket(proc_kill_sock_path)
			if proc_kill_sock is None:
				log.error('Unable to connect to Process Kill socket')
				success &= False
				continue

			if not send_message(proc_kill_sock, p):
				log.error('Failed to send Immediate Process Kill message')
				success &= False
				continue

		# Send list of processes to netlink socket that the Virtue LSM is listening to, so that the LSM can block future attempts at starting the blocked process
                # TODO: uncomment this when the kernel updates have been checked in!
                """
		sock = connect_socket_netlink()
		if sock is None:
			log.error('Unable to connect to net socket')
			return False

		if not send_message_netlink(sock, config['processes']):
			log.error('Failed to send command over netlink socket')
			return False
                """

		return True

	elif transducer_id == 'block_net':
		chardev = "/dev/netblockchar"
		#WORK IN PROGRESS
		log.info('block_net actuator received configuration')

		if enabled == False:
			fd = os.open(chardev, os.O_RDWR)
			os.write(fd, "reset")
			os.close(fd)
			return True

		regexFormat = r'^((block|unblock){1}\s(incoming|outgoing){1}'
		regexFormat += r'\s(src|dst){1}\s(ipv4|ipv6|tcp|udp|ipport){1}\s)(.*)$'
		#These are used for accessing fields in the regular expression
		proto = 5
		value = 6

		portRegex = r'^[0-9]{1,5}$'
		ipv4Regex = r'^((\d{1,3}\.){3}\d{1,3})$'
		#IPv6 address must be expanded for now
		ipv6Regex = r'^(([0-9a-z]{4}\:){5}[0-9a-z]{4})$'
		ipportRegex = r'^(((\d{1,3}\.){3}\d{1,3})|(([0-9a-z]{4}\:){7}[0-9a-z]{4}))\:(\d{1,5})$'
		rules = []
		for j in config["rules"]:
			rules.append(str(j))

		validRules = []
		#Make sure all rules in the configuration are valid
		for rule in rules:
			rule = rule.replace('_',' ')
			if re.match(regexFormat, rule):
				g = re.search(regexFormat, rule)
				if g.group(proto) == 'tcp' or g.group(proto) == 'udp':
					v = re.search(portRegex, g.group(value))
					if v != None and int(v.group(0)) < 65536:
						validRules.append(rule)
						continue
					else:
						log.error('Invalid block_net actuator configuration (%s) for transducer %s', rule, transducer_id)
						return False
				elif g.group(proto) == 'ipv4':
					v = re.search(ipv4Regex, g.group(value))
					if v != None and all(int(i) <= 255 for i in v.group(0).split('.')):
						validRules.append(rule)
						continue
					else:
						log.error('Invalid block_net actuator configuration (%s) for transducer %s', rule, transducer_id)
						return False
				elif g.group(proto) == 'ipv6':
					v = re.search(ipv6Regex, g.group(value).lower())
					if v != None:
						validRules.append(rule)
						continue
					else:
						log.error('Invalid block_net actuator configuration (%s) for transducer %s', rule, transducer_id)
						return False
				elif g.group(proto) == 'ipport':
					v = re.search(ipportRegex, g.group(value).lower())
					if v!= None and int(v.group(6)) < 65536:
						if v.group(2) != None and all(int(i) < 255 for i in v.group(2).split('.')):
							validRules.append(rule)
							continue
						elif v.group(4) != None:
							validRules.append(rule)
							continue
						else:
							log.error('Invalid block_net actuator configuration (%s) for transducer %s', rule, transducer_id)
					else:
						log.error('Invalid block_net actuator configuration (%s) for transducer %s', rule, transducer_id)
				else:
					log.error('Invalid actuator configuration (%s)', rule)
					return False
			else:
				log.error('Invalid block_net actuator configuration (%s) for transducer %s', rule, transducer_id)
				return False

		#For now just delete current ruleset on new configuration
		fd = os.open(chardev, os.O_RDWR)
		os.write(fd, "reset")
		os.close(fd)
		#Write valid ruleset to character device
		for rule in validRules:
			fd = os.open(chardev, os.O_RDWR)
			os.write(fd, rule)
			os.close(fd)

		return True
	else:
		log.warning('This type of actuator has not been defined yet: %s', transducer_id)
		return False

def send_ack(virtue_id, transducer_id, transducer_type, config, enabled, timestamp, virtue_key, conn):
	# Confirm to excalibur that changes were successful
	new_signature = sign_message(virtue_id, transducer_id, transducer_type, config, enabled, timestamp, virtue_key)

	try:
		res = r.db('transducers').table('acks').insert({
			'id': [virtue_id, transducer_id],
			'virtue_id': virtue_id,
			'transducer_id': transducer_id,
			'type': transducer_type,
			'configuration': config,
			'enabled': enabled,
			'timestamp': timestamp,
			'signature': r.binary(new_signature)
		}, conflict='replace').run(conn)
		if res['errors'] > 0:
			log.error('Failed to insert into ACKs table; first error: %s', str(res['first_error']))
			return False
	except r.ReqlError as e:
		log.error('Failed to publish ACK to Excalibur because: %s', str(e))
		return False
	return True

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
		required_keys = ['virtue_id', 'transducer_id', 'type', 'configuration', 
                        'enabled', 'timestamp', 'signature']
		if not all( [ (key in row) for key in required_keys ] ):
                        log.error('Missing required keys in row: %s',\
                                str(filter((lambda key: key not in row),required_keys)))
			continue
		transducer_id = row['transducer_id']
		transducer_type = row['type']
		config = row['configuration']
		enabled = row['enabled']
		timestamp = row['timestamp']
		signature = row['signature']

		# Validate message's signature
		printable_msg = deepcopy(row)
		del printable_msg['signature']
		if verify_message(virtue_id, transducer_id, transducer_type, config, enabled, timestamp, signature, excalibur_key):
			log.info('Received valid command message: %s', \
				json.dumps(printable_msg, indent=2))
		else:
			log.error('Unable to validate signature of command message: %s', \
				json.dumps(printable_msg, indent=2))
			continue

		if transducer_type == 'ACTUATOR':

			if do_actuator(transducer_id, config, enabled) == False:
				continue

			send_ack(virtue_id, transducer_id, transducer_type, config, enabled, timestamp, virtue_key, conn)

			continue

			# TODO ideally the giant block below would live in a separate function and this would be a tidy little if/else
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

			send_ack(virtue_id, transducer_id, transducer_type, config, enabled, timestamp, virtue_key, conn)
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
	parser.add_argument('-s', '--socket', help='Path to socket to filter', default='/var/run/receiver_to_filter')
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

	heartbeat_thread = Thread(target = heartbeat, args=(
		args.virtue_id, args.rdb_host, args.ca_cert, args.heartbeat, 
		virtue_key, args.socket,))
	heartbeat_thread.start()

	listen_for_commands(args.virtue_id, excalibur_key, virtue_key, args.rdb_host, args.socket)

