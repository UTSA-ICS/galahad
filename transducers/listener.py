#!/usr/bin/env python2

###############################################################################
#
# Heartbeat Listener
# Listens for heartbeats coming from Merlin, and alerts ElasticSearch if
# something is wrong.
#
# Copyright (c) 2018 by Raytheon BBN Technologies Corp.
#
###############################################################################

import argparse
import configparser
import cmd
import gnureadline as readline
import json
import logging
import os.path
import rethinkdb as r
import sys
import traceback
import urllib3
import urllib3.contrib.pyopenssl
from copy import deepcopy
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from datetime import datetime
from elasticsearch_dsl import DocType, Date, Integer, Keyword, Text
from elasticsearch_dsl.connections import connections
from time import sleep, time

class HeartbeatListener():

	def __init__(self, dotfile):
		# Dotfile path
		self.dotfile = dotfile

		# Default values
		self.rethinkdb_host = 'ec2-54-145-211-31.compute-1.amazonaws.com'
		self.rdb_ca_cert = 'rethinkdb_cert.pem'
		self.excalibur_key_file = 'excalibur_key.pem'
		self.virtue_key_dir = '.'
		self.es_host = '172.30.1.182'
		self.es_ca_cert = 'chain-ca.pem'
		self.es_client_cert = 'kirk.crtfull.pem'
		self.es_client_key = 'kirk.key.pem'
		self.max_time = 3 * 60   # 3 minutes
		self.logfile = 'listener.log'

		self.log = logging.getLogger('heartbeatlistener')

	# ---------------------------------------------------

	def setup_logging(self, filename):
		logfile = logging.FileHandler(filename)
		formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		logfile.setFormatter(formatter)
		self.log.addHandler(logfile)
		self.log.setLevel(logging.INFO)

	# ---------------------------------------------------

	def setup_config(self):
		self.log.info('Reading config')
		# Read config file if exists
		if os.path.isfile(self.dotfile):
			config = configparser.ConfigParser()
			config.read(self.dotfile)
			if 'transducer' in config:
				c = config['transducer']

				if 'logfile' in c:
					self.logfile = c['logfile']
				# Setup logging either for specified or default file name
				self.setup_logging(self.logfile)

				if 'rethinkdb_host' in c:
					self.rethinkdb_host = c['rethinkdb_host']
				if 'rethinkdb_ca_cert' in c:
					self.rdb_ca_cert = c['rethinkdb_ca_cert']
				if 'excalibur_private_key' in c:
					self.excalibur_key_file = c['excalibur_private_key']
				if 'virtue_public_key_dir' in c:
					self.virtue_key_dir = c['virtue_public_key_dir']
				if 'elasticsearch_host' in c:
					self.es_host = c['elasticsearch_host']
				if 'elasticsearch_ca_cert' in c:
					self.es_ca_cert = c['elasticsearch_ca_cert']
				if 'elasticsearch_client_cert' in c:
					self.es_client_cert = c['elasticsearch_client_cert']
				if 'elasticsearch_client_key' in c:
					self.es_client_key = c['elasticsearch_client_key']
				if 'max_time' in c:
					try:
						self.max_time = int(c['max_time'])
					except:
						self.log.error('Invalid number for max time: %s; using default: %d', str(c['max_time']), self.max_time)


		# Check that files exist
		if not os.path.isfile(self.rdb_ca_cert):
			self.log.error('File not found for RethinkDB CA cert: %s', self.rdb_ca_cert)
			return False
		if not os.path.isfile(self.excalibur_key_file):
			self.log.error('File not found for Excalibur private key: %s', self.excalibur_key_file)
			return False
		if not os.path.isdir(self.virtue_key_dir):
			self.log.error('Directory not found for Virtue public keys: ', self.virtue_key_dir)
			return False
		if not os.path.isfile(self.es_ca_cert):
			self.log.error('File not found for Elasticsearch CA cert: ', self.es_ca_cert)
			return False
		if not os.path.isfile(self.es_client_cert):
			self.log.error('File not found for Elasticsearch client cert: ', self.es_client_cert)
			return False
		if not os.path.isfile(self.es_client_key):
			self.log.error('File not found for Elasticsearch client key: ', self.es_client_key)
			return False
		if self.max_time <= 0:
			self.log.error('Max time invalid: %d', self.max_time)
			return False

		return True

	# ---------------------------------------------------

	def connect_rethinkdb(self):
		self.log.info('Connecting to RethinkDB')
		# RethinkDB connection
		while (True):
			with open(self.excalibur_key_file, 'r') as f:
				key = f.read()
				excalibur_key = RSA.importKey(key)
				try:
					conn = r.connect(host=self.rethinkdb_host, 
						user='excalibur', 
						password=key ,
						ssl={ 'ca_certs': self.rdb_ca_cert })
					return conn
				except r.ReqlDriverError as e:
					self.log.error('Failed to connect to RethinkDB at host: %s; error: %s; Trying again in 30 seconds.', self.rethinkdb_host, str(e))
					sleep(30)

	# ---------------------------------------------------

	def __verify_message(self, row):
		if row is None:
			self.log.error('No match found')
			return False

		required_keys = ['virtue_id', 'transducer_id', 'configuration', 
			'enabled', 'timestamp', 'signature']
		if not all( [ (key in row) for key in required_keys ] ):
			self.log.error('Missing required keys in row: %s',\
				str(filter((lambda key: key not in row),required_keys)))
			return False

		message = '|'.join([row['virtue_id'], row['transducer_id'], 
			str(row['configuration']), str(row['enabled']), str(row['timestamp'])])

		virtue_public_key = os.path.join(self.virtue_key_dir, 
			'virtue_' + row['virtue_id'] + '_pub.pem')
		if not os.path.isfile(virtue_public_key):
			self.log.error('No file found for Virtue public key at: %s', \
				virtue_public_key)
			return False
		with open(virtue_public_key) as f:
			virtue_key = RSA.importKey(f.read())

		h = SHA.new(str(message))
		verifier = PKCS1_v1_5.new(virtue_key)
		verified = verifier.verify(h, row['signature'])
		if not verified:
			printable_msg = deepcopy(row)
			del printable_msg['signature']
			self.log.error('Unable to validate signature of ACK message: %s', \
				json.dumps(printable_msg, indent=2))
		return verified

	# ---------------------------------------------------

	# Create ES connection
	def connect_es(self):
		self.log.info('Connecting to ElasticSearch')
		while (True):
			try:
				urllib3.contrib.pyopenssl.inject_into_urllib3()
				connections.create_connection(
					hosts = [ self.es_host ],
					use_ssl = True,
					verify_certs = True,
					http_auth = ('admin', 'admin'),
					ca_certs = self.es_ca_cert,
					# PEM formatted SSL client certificate
					client_cert = self.es_client_cert,
					# PEM formatted SSL client key
					client_key = self.es_client_key
				)
				return
			except Exception as e:
				self.log.error('Could not connect to ElasticSearch: %s; Trying again in 30 seconds.', str(e))
				sleep(30)
		HeartbeatNotification.init()

	# ---------------------------------------------------

	# Format of elasticsearch messages
	class HeartbeatNotification(DocType):
		message = Keyword()
		virtue = Keyword()
		row = Keyword()
		timestamp = Date()

		class Meta:
			index = "transducer"

	# ---------------------------------------------------

	def alert_elasticsearch(self, message, row, virtue):
		notification = self.HeartbeatNotification(message = message, row = row, virtue = virtue, timestamp = datetime.now())
		notification.save()

	# ---------------------------------------------------

	def run(self):
		self.log.info('Starting')

		# If no heartbeats for >= `interval` seconds, send an alert to Elasticsearch
		interval = self.max_time   # default is 3 minutes

		if not self.setup_config():
			self.log.error('Configuration errors - exiting')
			sys.exit(1)

		# These will loop until they get connections, so they can't "fail"
		conn = self.connect_rethinkdb()
		self.connect_es()

		self.log.info('Starting to listen for heartbeats')
		while (True):
			current_time = int(time())

			for row in r.db('transducers').table('acks').run(conn):
				printable_msg = deepcopy(row)
				del printable_msg['signature']

				if not self.__verify_message(row):
					self.alert_elasticsearch("Invalid signature for row",json.dumps(printable_msg), row['virtue_id'])
				if current_time > row['timestamp'] + interval:
					self.alert_elasticsearch("Missing heartbeats for more than 3 minutes!", json.dumps(printable_msg), row['virtue_id'])
			sleep(30)  # some amount of time

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Listener for Virtue transducer heartbeats')
	parser.add_argument('dotfile', help='The .excalibur file containing all parameters', default='.excalibur')
	args = parser.parse_args()

	HeartbeatListener(args.dotfile).run()

