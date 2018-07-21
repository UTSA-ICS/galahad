#!/usr/bin/python
import sys
import subprocess
import rethinkdb as r
import socket
import threading

from gaius.rethink import Rethink
from gaius.migration import Migrate

rethink = Rethink()
migrate = Migrate()

#test for all changes and starts the start file with argument saying what type of insert it is if something is inserted
class changes():
	#what it should do if an object whose function is compute is inserted
        def compute(self):
                r.connect("172.30.93.138",28015).repl()
		computecursor = r.db("routing").table("galahad").changes().filter(lambda change: \
			(change["old_val"] == None) and (change["new_val"]["function"]=="compute")).run().next()
                with open("pass.txt", "w") as testfile:
                        testfile.write(str(computecursor))
                print subprocess.Popen("./start compute", shell=True, stdout=subprocess.PIPE).stdout.read()

        #what it should do if an object whose function is virtue is inserted
        def virtue_new(self):
                r.connect("172.30.93.138",28015).repl()
		virtuecursor = r.db("routing").table("galahad").changes().filter(lambda change: \
			(change["old_val"] == None) and (change["new_val"]["function"]=="virtue")).run()
		for virtue in virtuecursor:
			valor = rethink.filter('galahad', 
				{'address'	: virtue['new_val']['address'],
				 'function'	: 'valor'}).next()
			print valor
			migrate.start_instance(virtue["new_val"]["host"], virtue["new_val"]["guestnet"], \
				valor["guestnet"])
	def virtue_migrate(self):
		r.connect("172.30.93.138",28015).repl()
		cursor = r.db('routing').table('transducer').changes().filter(lambda change: \
			(change['old_val']['flag']=='FALSE') & (change['new_val']['flag']=='TRUE')).run()
		for flag in cursor:
			host = flag['new_val']['config']['host']
			newHost = flag['new_val']['config']['newHost']
			dest = rethink.filter('galahad', {'host':newHost}).next()
			# migrate.sh host dest['address']
			migrate.migrate_instance(host, dest['address'])
			old = rethink.filter('galahad',
				{'function':'virtue',
				 'host':host}).next()
			oldValor = rethink.filter('galahad',
				{'function'	: 'valor',
				 'address'	: old['address']}).next()
			history = flag['new_val']['history']
			history.append(oldValor['host'])
			print flag
			# update virtue object

	def virtue_cleanup(self):
		r.connect("172.30.93.138",28015).repl()
		cursor = r.db('routing').table('galahad').changes().filter(lambda change: \
			(change['old_val']['function']=='virtue') & (change['new_val']==None)).run()
		for virtue in cursor:
			# cleanup.sh virtue['old_val']['host']
			migrate.cleanup_instance(virtue["old_val"]["host"])
			print virtue['old_val']['host']
			print virtue

        #what it should do if an object whose function is valor is inserted
        def valor(self):
                r.connect("172.30.93.138",28015).repl()
                hostname = socket.gethostname()
                IPAddr = socket.gethostbyname(hostname)
                valorcursor = r.db("routing").table("galahad").changes().filter(lambda change: \
			(change["old_val"] == None) and (change["new_val"]["function"]=="valor")).run().next()
                if valorcursor["new_val"]["address"] == IPAddr:
                        return
                else:
                        with open("pass.txt", "w") as testfile:
                                testfile.write(str(valorcursor))
                        print subprocess.Popen("./start valor", shell=True, stdout=subprocess.PIPE).stdout.read()

	#tests everything at once
        def main(self):
                while True:
			#computeThread = threading.Thread(target=self.compute)
                        virtueThread = threading.Thread(target=self.virtue_new)
			virtueMigrate = threading.Thread(target=self.virtue_migrate)
			virtueCleanup = threading.Thread(target=self.virtue_cleanup)
                        #valorThread = threading.Thread(target=self.valor)
                        #try:
                        #        computeThread.start()
                        #except:
                        #        pass
                        try:
                                virtueThread.start()
                        except:
                                pass
			try:
				virtueMigrate.start()
			except:
				pass
			try:
				virtueCleanup.start()
			except:
				pass
			#try:
                        #        valorThread.start()
                        #except:
                        #        pass
                        #computeThread.join()
                        virtueThread.join()
			virtueMigrate.join()
			virtueCleanup.join()
                        #valorThread.join()

if __name__ == "__main__":
	c = changes()
	c.main()
