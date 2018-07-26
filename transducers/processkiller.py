import grp
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

try:
    os.unlink(socket_address)
except OSError:
    if os.path.exists(socket_address):
        raise

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

sock.bind(socket_address)

os.chown(socket_address, os.getuid(), grp.getgrnam('camelot').gr_gid)
os.chmod(socket_address, 0770)

sock.listen(1)

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

        if all_data != '':
            all_data = cleanup.sub('', all_data)
            success = False
            try:
                subprocess.check_call(['killall', '-9', str(all_data)])
                success = True
            except subprocess.CalledProcessError as e:
                success = False

            if success:
                try:
                    subprocess.check_call(['logger', 'LogType: Merlin TransducerId: proc_kill Action: ImmediatelyKilled Proc: "' + str(all_data) + '"'])
                except subprocess.CalledProcessError as e:
                    pass

    finally:
        connection.close()
