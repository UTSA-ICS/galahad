# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

from ldaplookup import LDAP
from services.errorcodes import ErrorCodes
from . import ldap_tools
import json
import os.path
import time
from copy import deepcopy

import rethinkdb as r

from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA

DEBUG_PERMISSIONS = False


class EndPoint_Security:
    def __init__(self, user, password):
        self.inst = LDAP(user, password)

        self.inst.bind_ldap()

        if not hasattr(self.__class__, 'conn'):
            self.__class__.conn = None

    # Not officially part of the API but necessary to set up paths correctly
    def set_api_config(self, config):
        # Default values
        self.__class__.rethinkdb_host = 'rethinkdb.galahad.lab'
        self.__class__.ca_cert = 'rethinkdb_cert.pem'
        self.__class__.excalibur_key_file = 'excalibur_key.pem'
        self.__class__.virtue_key_dir = '.'
        self.__class__.wait_for_ack = 30  # seconds


        if 'transducer' in config:
            c = config['transducer']
            if 'rethinkdb_host' in c:
                self.__class__.rethinkdb_host = c['rethinkdb_host']
            if 'rethinkdb_ca_cert' in c:
                self.__class__.ca_cert = c['rethinkdb_ca_cert']
            if 'excalibur_private_key' in c:
                self.__class__.excalibur_key_file = c['excalibur_private_key']
            if 'virtue_public_key_dir' in c:
                self.__class__.virtue_key_dir = c['virtue_public_key_dir']
            if 'wait_for_ack' in c:
                try:
                    self.__class__.wait_for_ack = int(c['wait_for_ack'])
                except:
                    return self.__error(
                        'unspecifiedError',
                        details=
                        'Invalid number for seconds to wait for Transducer control ACK: {}; using default: {} seconds'.
                        format(c['wait_for_ack'], self.__class__.wait_for_ack))

        # Check that files exist
        if not os.path.isfile(self.__class__.ca_cert):
            return self.__error(
                'invalidOrMissingParameters',
                details='File not found for RethinkDB CA cert: ' +
                self.__class__.ca_cert)
        if not os.path.isfile(self.__class__.excalibur_key_file):
            return self.__error(
                'invalidOrMissingParameters',
                details='File not found for Excalibur private key: ' +
                self.__class__.excalibur_key_file)
        if not os.path.isdir(self.__class__.virtue_key_dir):
            return self.__error(
                'invalidOrMissingParameters',
                details='Directory not found for Virtue public keys: ' +
                self.__class__.virtue_key_dir)
        return self.__error('success')

    def transducer_list(self):
        '''
        Lists all transducers currently available in the system

        Args:

        Returns:
            list: Transducer objects for known transducers
        '''

        try:
            transducers_raw = self.inst.get_objs_of_type('OpenLDAPtransducer')
            if transducers_raw is None:
                return self.__error(
                    'unspecifiedError',
                    details='Unable to get transducer objects from LDAP')

            transducers_ret = []

            for transducer in transducers_raw:
                ldap_tools.parse_ldap(transducer[1])
                transducers_ret.append(transducer[1])

            return json.dumps(transducers_ret)

        except Exception as e:
            return self.__error(
                'unspecifiedError',
                details='Unable to get transducer objects: ' + str(e))

    def transducer_get(self, transducerId):
        '''
        Gets information about the indicated Transducer. Does not include information about any
        instantiation in Virtues.

        Args:
            transducerId (str): The ID of the Transducer to get.

        Returns:
            Transducer: information about the indicated transducer
        '''

        try:
            transducer = self.inst.get_obj('cid', transducerId,
                                           'openLDAPtransducer', True)
            if transducer is None or transducer == ():
                return self.__error('invalidTransducerId')
            ldap_tools.parse_ldap(transducer)

            if DEBUG_PERMISSIONS:
                return json.dumps(transducer)

            return json.dumps(transducer)

        except Exception as e:
            return self.__error(
                'unspecifiedError',
                details='Unable to get transducer object: ' + str(e))

    def transducer_enable(self, transducerId, virtueId, configuration):
        '''
        Enables the indicated Transducer in the indicated Virtue.

        Args:
            transducerId (str) : The ID of the Transducer to enable. 
            virtueId (str)     : The ID of the Virtue in which to enable the Transducer. 
            configuration (object): The configuration to apply to the Transducer when it is enabled. Format 
                        is Transducer-specific. This overrides any existing configuration with the same keys.

        Returns:
            bool: True if the transducer was enabled, false otherwise

        '''
        ret = self.__enable_disable(transducerId, virtueId, configuration,
                                     True)
        if type(ret) is bool and ret == True:
            return self.__error('success')
        return ret

    def transducer_disable(self, transducerId, virtueId):
        '''
        Disables the indicated Transducer in the indicated Virtue

        Args:
            transducerId (str) : The ID of the Transducer to disable
            virtueId (str)     : The ID of the Virtue in which to enable the Transducer. 

        Returns:
            bool: True if the transducer was enabled, false otherwise
        '''
        ret = self.__enable_disable(transducerId, virtueId, None, False)
        if type(ret) is bool and ret == True:
            return self.__error('success')
        return ret

    def transducer_get_enabled(self, transducerId, virtueId):
        '''
        Gets the current enabled status for the indicated Transducer in the indicated Virtue.

        Args:
            transducerId (str) : The ID of the Transducer
            virtueId (str)     : The ID of the Virtue in which to enable the Transducer. 

        Returns:
            bool: True if the Transducer is enabled in the Virtue, false if it is not

        '''

        if self.__class__.conn is None:
            self.__connect_rethinkdb()
        try:
            row = r.db('transducers').table('acks')\
                .get([virtueId, transducerId]).run(self.__class__.conn)
        except r.ReqlError as e:
            return self.__error(
                'unspecifiedError',
                details='Failed to get info about transducer: ' + str(e))

        # Transducers are enabled by default
        if row is None:
            return json.dumps( { 'enabled': True } )

        self.__verify_message(row)
        return json.dumps( { 'enabled': row['enabled'] } )

    def transducer_get_configuration(self, transducerId, virtueId):
        '''
        Gets the current configuration for the indicated Transducer in the indicated Virtue.

        Args:
            transducerId (str) : The ID of the Transducer
            virtueId (str)     : The ID of the Virtue in which to enable the Transducer. 

        Returns:
            TransducerConfig: Configuration information for the indicated Transducer in the indicated Virtue
        '''

        if self.__class__.conn is None:
            self.__connect_rethinkdb()
        try:
            row = r.db('transducers').table('acks')\
                .get([virtueId, transducerId]).run(self.__class__.conn)
        except r.ReqlError as e:
            return self.__error(
                'unspecifiedError',
                details='Failed to get info about transducer: ' + str(e))

        # If there's no row, there's no set config
        if row is None:
            return json.dumps( None )

        self.__verify_message(row)
        # By definition, the configuration is a JSON object
        return row['configuration']

    def transducer_list_enabled(self, virtueId):
        '''
        Lists all Transducers currently that are currently enabled in the indicated Virtue.

        Args:
            virtueId (str)     : The ID of the Virtue in which to enable the Transducer. 

        Returns:
            list(Transducer): List of enabled transducers within the specified Virtue
        '''

        enabled_transducers = []

        if self.__class__.conn is None:
            self.__connect_rethinkdb()
        try:
            for row in r.db('transducers').table('acks')\
                .filter( { 'virtue_id': virtueId } ).run(self.__class__.conn):

                self.__verify_message(row)
                if ('enabled' in row) and row['enabled']:
                    enabled_transducers.append(row['transducer_id'])

        except r.ReqlError as e:
            return self.__error(
                'unspecifiedError',
                details='Failed to get enabled transducers: ' + str(e))

        return json.dumps(enabled_transducers)

    def __connect_rethinkdb(self):
        # RethinkDB connection
        # This connection will fail if setup_rethinkdb.py hasn't been run, because
        # there won't be an excalibur user and it won't have the specified password.
        with open(self.__class__.excalibur_key_file, 'r') as f:
            key = f.read()
            self.__class__.excalibur_key = RSA.importKey(key)
            try:
                self.__class__.conn = r.connect(
                    host=self.__class__.rethinkdb_host,
                    user='excalibur',
                    password=key,
                    ssl={'ca_certs': self.__class__.ca_cert})
            except r.ReqlDriverError as e:
                return self.__error('unspecifiedError', details=\
                    'Failed to connect to RethinkDB at host: ' + \
                    self.__class__.rethinkdb_host + ' because: ' + str(e))
        return True

    def __enable_disable(self, transducerId, virtueId, configuration,
                         isEnable):

        # Make sure transducer exists
        transducer = self.inst.get_obj('cid', transducerId,
                                       'openLDAPtransducer', True)
        if transducer is None or transducer == ():
            return self.__error('invalidTransducerId')

        transducerType = transducer['ctype']

        # Make sure virtue exists
        virtue = self.inst.get_obj('cid', virtueId, 'openLDAPvirtue', True)
        if virtue is None or virtue == ():
            return self.__error('invalidVirtueId')

        # Change the ruleset
        ret = self.__change_ruleset(
            virtueId, transducerId, transducerType, isEnable, config=configuration)
        if ret != True:
            return ret

        # Update the virtue's list of transducers
        new_t_list = self.transducer_list_enabled(virtueId)
        if type(new_t_list) is dict and new_t_list['status'] == 'failed':
            # Couldn't retrieve new list of transducers
            return self.__error(
                'unspecifiedError',
                details='Unable to update virtue\'s list of transducers')
            
        virtue['ctransIds'] = str(new_t_list)
        ret = self.inst.modify_obj('cid', virtueId, virtue, 'OpenLDAPvirtue',
                                   True)
        if ret != 0:
            return self.__error(
                'unspecifiedError',
                details='Unable to update virtue\'s list of transducers')

        return True

    def __sign_message(self, row):
        required_keys = [
            'virtue_id', 'transducer_id', 'type', 'configuration', 
            'enabled', 'timestamp'
        ]
        if not all([(key in row) for key in required_keys]):
            return (False, 
                self.__error('unspecifiedError', details='Missing required keys in row: ' +\
                str(filter((lambda key: key not in row),required_keys))))

        message = '|'.join([
            row['virtue_id'], row['transducer_id'], row['type'],
            str(row['configuration']),
            str(row['enabled']),
            str(row['timestamp'])
        ])
        h = SHA.new(str(message))
        signer = PKCS1_v1_5.new(self.__class__.excalibur_key)
        signature = signer.sign(h)
        return (True, signature)

    def __verify_message(self, row):
        if row is None:
            return self.__error(
                'unspecifiedError', details='No match found in database')

        required_keys = [
            'virtue_id', 'transducer_id', 'type', 'configuration',
            'enabled', 'timestamp', 'signature'
        ]
        if not all([(key in row) for key in required_keys]):
            return self.__error('unspecifiedError', details='Missing required keys in row: ' +\
                str(filter((lambda key: key not in row),required_keys)))

        message = '|'.join([
            row['virtue_id'], row['transducer_id'], row['type'],
            str(row['configuration']),
            str(row['enabled']),
            str(row['timestamp'])
        ])

        virtue_public_key = os.path.join(
            self.__class__.virtue_key_dir,
            'virtue_' + row['virtue_id'] + '_pub.pem')
        if not os.path.isfile(virtue_public_key):
            return self.__error('invalidOrMissingParameters', details=\
                'No file found for Virtue public key at: ' + \
                virtue_public_key)
        with open(virtue_public_key) as f:
            virtue_key = RSA.importKey(f.read())

        h = SHA.new(str(message))
        verifier = PKCS1_v1_5.new(virtue_key)
        verified = verifier.verify(h, row['signature'])
        if not verified:
            printable_msg = deepcopy(row)
            del printable_msg['signature']
            return self.__error('unspecifiedError', details=\
                'Unable to validate signature of ACK message: ' + \
                json.dumps(printable_msg, indent=2))

    def __change_ruleset(self, virtue_id, trans_id, transducer_type, enable, config=None):
        if self.__class__.conn is None:
            ret = self.__connect_rethinkdb()
            # Return if error
            if ret != True:
                return ret

        if type(transducer_type) is list:
            transducer_type = transducer_type[0]

        timestamp = int(time.time())

        row = {
            'id': [virtue_id, trans_id],
            'virtue_id': virtue_id,
            'transducer_id': trans_id,
            'type': transducer_type,
            'configuration': config,
            'enabled': enable,
            'timestamp': timestamp
        }
        (success, signature) = self.__sign_message(row)
        if not success:
           # Return error code
           return signature

        row['signature'] = r.binary(signature)

        # Send command to change ruleset
        try:
            res = r.db('transducers').table('commands')\
                .insert(row, conflict='replace').run(self.__class__.conn)
            if res['errors'] > 0:
                return self.__error(
                    'unspecifiedError',
                    details='Failed to insert into commands table; first error: '
                    + res['first_error'])
        except r.ReqlError as e:
            return self.__error(
                'unspecifiedError',
                details='Failed to insert into commands table: ' + str(e))

        # Wait for ACK from the virtue that the ruleset has been changed
        #try:
        cursor = r.db('transducers').table('acks')\
            .get([virtue_id, trans_id])\
            .changes(squash=False).run(self.__class__.conn)
        #except r.ReqlError as e:
        #       print 'ERROR: Failed to read from the ACKs table because:', e
        #       return False

        retry = True
        while retry:
            try:
                retry = False
                # Wait max 30 seconds - if we miss the real ACK, hopefully
                # at least the next heartbeat will suffice
                print 'INFO: Waiting for ACK'
                change = cursor.next(wait=self.__class__.wait_for_ack)
                row = change['new_val']
                self.__verify_message(row)
                if row['timestamp'] >= timestamp:
                    if row['enabled'] == enable:
                        print 'INFO: ACK received!'
                        return True
                    else:
                        return self.__error(
                            'unspecifiedError',
                            details=
                            'Received ACK with incorrect value for enabled: ' +
                            str(enable) + ' vs ' + str(row['enabled']))
                else:
                    print 'WARN: Timestamp incorrect:', timestamp, row[
                        'timestamp']
                    # Retry once in case that was just a wayward ACK
                    retry = True

            except (r.ReqlCursorEmpty, r.ReqlDriverError) as e:
                return self.__error(
                    'unspecifiedError',
                    details='Failed to receive ACK before timeout')
            finally:
                cursor.close()
        return self.__error(
            'unspecifiedError', details='Failed to receive ACK before timeout')

    def __error(self, key, details=None):
        if key not in ErrorCodes.security:
            print "Error type '" + key + "' not found!  Using UnspecifiedError."
            key = 'unspecifiedError'
        e = deepcopy(ErrorCodes.security[key])
        if details is not None:
            #e['details'] = details
            e['result'].append(details)
        return json.dumps(e)
