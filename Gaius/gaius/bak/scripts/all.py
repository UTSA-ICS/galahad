#!/usr/bin/python
import socket
import time
import subprocess

s = socket.socket()
port = 12345
var = False

#start instance
print subprocess.Popen("/home/ubuntu/galahad/gaius/gaius/scripts/add.py", shell=True, stdout=subprocess.PIPE).stdout.read()
time.sleep(120)

#migrate instance
print subprocess.Popen("/home/ubuntu/galahad/gaius/gaius/scripts/transducer.py", shell=True, stdout=subprocess.PIPE).stdout.read()

#wait until migration is done
while True:
        try:
                s.connect(('', port))
                var = s.recv(1024)
                s.close()
        except:
                pass
        if var == "TRUE":
                break

#cleanup instance
print subprocess.Popen("/home/ubuntu/galahad/gaius/gaius/scripts/remove.py", shell=True, stdout=subprocess.PIPE).stdout.read()

