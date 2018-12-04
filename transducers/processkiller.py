import grp
import logging
import os
import re
import socket
import subprocess
import sys

# This reads process names from a socket and kills those processes.  
# It also logs a successful kill to syslog.
# The socket is written to by Merlin.

socket_address = '/var/run/deathnote'
cleanup = re.compile('[^a-zA-Z0-9-_]')

# Logging setup
log = logging.getLogger('processkiller')
logfile = logging.FileHandler('/opt/processkiller/processkiller.log')

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
logfile.setFormatter(formatter)
log.addHandler(logfile)
log.setLevel(logging.INFO)

log.info('Started ProcessKiller')

try:
    os.unlink(socket_address)
except OSError:
    log.error('Could not delete existing copy of socket: ' + str(socket_address))
    if os.path.exists(socket_address):
        raise

try:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    sock.bind(socket_address)

    os.chown(socket_address, os.getuid(), grp.getgrnam('camelot').gr_gid)
    os.chmod(socket_address, 0770)

    sock.listen(1)
except Exception as e:
    log.error('Failed to connect to socket: ' + str(e))
    sys.exit(1)

log.info('Successfully connected to socket')

while True:
    connection, client_address = sock.accept()
    try:
	all_data = ''
        while True:
            data = connection.recv(256)
            if data:
                all_data += data
            else:
                break
        log.info('Received message: ' + all_data)

        if all_data != '':
            all_data = cleanup.sub('', all_data)
            success = False
            try:
                subprocess.check_call(['killall', '-9', str(all_data)])
                success = True
            except subprocess.CalledProcessError as e:
                log.error('Failed to kill because: ' + str(e))
                success = False

            if success:
                log.info('Succeeded in killing: ' + str(all_data))
                try:
                    subprocess.check_call(['logger', 'LogType: Merlin TransducerId: proc_kill Action: ImmediatelyKilled Proc: "' + str(all_data) + '"'])
                except subprocess.CalledProcessError as e:
                    log.error('Failed to log kill success to syslog because: ' + str(e))
    except Exception as e:
        log.error('Unknown exception: ' + str(e))
    finally:
        connection.close()
