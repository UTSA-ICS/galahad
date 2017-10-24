#nohup xpra start ssh/kelli@kelli-test-xpra2 --start-child=xterm > script.log 2>&1 &

"""
potential Windows equivalent - start /b *command*
"""

from	multiprocessing				import Process

if __name__ == '__main__':
	p = Process(target=bash, args=['xpra','start','ssh/kelli@kelli-test-xpra2','--start-child=xterm'])
	p.start()
