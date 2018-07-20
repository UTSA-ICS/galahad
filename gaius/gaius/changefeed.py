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

s = socket.socket()
port = 12345

#watch for changes to the table and start, migrate, and cleanup instances accourdionly
class changes():
	def __init__(self):
		hostname = socket.gethostname()
		IPAddr = socket.gethostbyname(hostname)
		self.IP = IPAddr

        def compute(self):
                r.connect("172.30.93.138",28015).repl()
		computecursor = r.db("routing").table("galahad").changes().filter(lambda change: \
			(change["old_val"] == None) and (change["new_val"]["function"]=="compute")).run().next()
                with open("pass.txt", "w") as testfile:
                        testfile.write(str(computecursor))
                print subprocess.Popen("./start compute", shell=True, stdout=subprocess.PIPE).stdout.read()

        def virtue_new(self):
                r.connect("172.30.93.138",28015).repl()
		virtuecursor = r.db("routing").table("galahad").changes().filter(lambda change: \
			(change["old_val"] == None) and (change["new_val"]["function"]=="virtue")).run()
		for virtue in virtuecursor:
			valor = rethink.filter('galahad',
				{'address'	: virtue['new_val']['address'],
				 'function'	: 'valor'}).next()
			if virtue["new_val"]["address"] == self.IP:
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
			object = rethink.filter("galahad", {"host":host}).next()
			if object["address"] == self.IP:
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

	def virtue_alert(self):
		r.connect("172.30.93.138",28015).repl()
                cursor = r.db('routing').table('transducer').changes().filter(lambda change: \
                        (change['old_val']['flag']=='TRUE') & (change['new_val']['flag']=='FALSE')).run()
                for flag in cursor:
                        host = flag['new_val']['config']['host']
                        newHost = flag['new_val']['config']['newHost']
                        dest = rethink.filter('galahad', {'host':newHost}).next()
			print "TEST1"
			#s.bind(('', port))
			#s.listen(5)
			#while True:
                        #        c, addr = s.accept()
                        #        c.send("TRUE")
                        #        c.close()
                        #        break
                        #print dest["address"]
			#print self.IP
			print dest["address"]
			if dest["address"] == self.IP:
				print "TEST2"
				r.db("routing").table("galahad").filter(r.row["host"]==host).update({"address": dest["address"]}).run()
                                config = {'host':host,'newHost':'TestNode.101'}
                                r.db("routing").table("transducer").filter(r.row["config"]["host"]==host).update({"config" : config}).run()
				print subprocess.Popen("xl create ./config/" + host + ".cfg", shell=True, stdout=subprocess.PIPE).stdout.read()

	def virtue_cleanup(self):
		r.connect("172.30.93.138",28015).repl()
		cursor = r.db('routing').table('galahad').changes().filter(lambda change: \
			(change['old_val']['function']=='virtue') & (change['new_val']==None)).run()
		for virtue in cursor:
			if virtue["old_val"]["address"] == self.IP:
				migrate.cleanup_instance(virtue["old_val"]["host"])
				print virtue['old_val']['host']
				print virtue

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

        def main(self):
                while True:
			#computeThread = threading.Thread(target=self.compute)
                        virtueThread = threading.Thread(target=self.virtue_new)
			virtueMigrate = threading.Thread(target=self.virtue_migrate)
			virtueAlert = threading.Thread(target=self.virtue_alert)
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
				virtueAlert.start()
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
			virtueAlert.join()
			virtueCleanup.join()
                        #valorThread.join()

if __name__ == "__main__":
	c = changes()
	c.main()
