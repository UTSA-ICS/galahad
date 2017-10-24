import	thread
import	time
import	subprocess, shlex
from	subprocess			import Popen, PIPE

flag = 0
def launch_proc():
	global flag
	flag += 1
	args = shlex.split("xpra start ssh/kelli@kelli-test-xpra2/1 --start-child=xterm")
	p = subprocess.Popen(args, shell=False, stdout=PIPE, stdin=PIPE)
	flag -= 1

def close_proc():
	global flag
	flag += 1
	args = shlex.split("xpra stop ssh/kelli@kelli-test-xpra2/1")
	p = subprocess.Popen(args, shell=False, stdout=PIPE, stdin=PIPE)
	flag -= 1

def launch_web():
	global flag
	flag += 1
	args = shlex.split("xpra start ssh/kelli@kelli-test-xpra2/2 --start-child=firefox")
	p = subprocess.Popen(args, shell=False, stdout=PIPE, stdin=PIPE)
	flag -= 1

thread.start_new_thread(launch_proc, ())
time.sleep(60)
thread.start_new_thread(close_proc, ())
time.sleep(10)
#thread.start_new_thread(launch_web, ())
#for i in range(10):
#	print(i)
#	time.sleep(10)

while flag > 0:
	pass

"""
def print_time(threadName, delay):
	count = 0
	while count < 5:
		time.sleep(delay)
		count += 1
		print "%s: %s" % (threadName, time.ctime(time.time()))

def start_proc(threadName, proc):
	

try:
	thread.start_new_thread(print_time, ("Thread-1", 2, ))
	thread.start_new_thread(print_time, ("Thread-2", 4, ))
except:
	print "Error: unable to start thread"

while 1:
	pass
"""
