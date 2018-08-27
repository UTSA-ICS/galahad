#!/usr/bin/python
import subprocess
import rethinkdb as r
import socket
import threading
import sys

#test for all changes and starts the start file with argument saying what type of insert it is if something is inserted
class changes():
	#what it should do if an object whose function is compute is inserted
        def compute(self):
                r.connect("172.30.93.138",28015).repl()
		computecursor = r.db("routing").table("galahad").changes().filter(lambda change: (change["old_val"] == None) and (change["new_val"]["function"]=="compute")).run().next()
                with open("pass.txt", "w") as testfile:
                                testfile.write(str(computecursor))
                print subprocess.Popen("./start compute", shell=True, stdout=subprocess.PIPE).stdout.read()

        #what it should do if an object whose function is unity is inserted
        def unity(self):
                r.connect("172.30.93.138",28015).repl()
		unitycursor = r.db("routing").table("galahad").changes().filter(lambda change: (change["old_val"] == None) and (change["new_val"]["function"]=="unity")).run().next()
                with open("pass.txt", "w") as testfile:
                                testfile.write(str(unitycursor))
                print subprocess.Popen("./start unity", shell=True, stdout=subprocess.PIPE).stdout.read()

        #what it should do if an object whose function is valor is inserted
        def valor(self):
                r.connect("172.30.93.138",28015).repl()
                hostname = socket.gethostname()
                IPAddr = socket.gethostbyname(hostname)
                valorcursor = r.db("routing").table("galahad").changes().filter(lambda change: (change["old_val"] == None) and (change["new_val"]["function"]=="valor")).run().next()
                if valorcursor["new_val"]["address"] == IPAddr:
                        return
                else:
                        with open("pass.txt", "w") as testfile:
                                testfile.write(str(valorcursor))
                        print subprocess.Popen("./start valor", shell=True, stdout=subprocess.PIPE).stdout.read()

	#tests everything at once
        def main(self):
                while True:
			computeThread = threading.Thread(target=self.compute)
                        unityThread = threading.Thread(target=self.unity)
                        valorThread = threading.Thread(target=self.valor)
                        try:
                                computeThread.start()
                        except:
                                pass
                        try:
                                unityThread.start()
                        except:
                                pass
			try:
                                valorThread.start()
                        except:
                                pass
                        computeThread.join()
                        unityThread.join()
                        valorThread.join()


