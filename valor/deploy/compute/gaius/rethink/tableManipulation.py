#!/usr/bin/env python
import rethinkdb as r
import socket
r.connect("172.30.93.138",28015).repl()
ip = socket.gethostbyname(socket.gethostname())

class EditingLibrary():
	#get the next available guestnet to use in insert
	def get_guestnet(self):
		highest_guestnet = r.db("routing").table("test").filter(lambda doc: (doc["function"] == "compute") or (doc["function"]=="valor")).order_by(r.desc("guestnet")).limit(1).run()
                old_guestnet = highest_guestnet[0]["guestnet"]
                new_guestnet = int(old_guestnet.rpartition('.')[-1]) + 1
                final_guestnet = old_guestnet.rpartition('.')[0] + "." + str(new_guestnet)
		return final_guestnet

	#insert an object into the database routing and table test
	def insert(self, function, address, guestnet, host):
		if function == "compute" or function == "valor" or function == "unity":
			r.db("routing").table("test").insert([
                                { "function": function, "address": address, "guestnet": self.get_guestnet(), "host": host
                                }
                        ]).run()
		else:
			r.db("routing").table("test").insert([
                       		{ "function": function, "address": address, "guestnet": guestnet, "host": host
                        	}
       			]).run()

	#delete an object in the database routing and table test
        def delete(self, field, var):
                r.db("routing").table("test").filter(r.row[field]==var).delete().run()

	#modify an object in the database routing and table test
        def modify(self, field, current, new):
                r.db("routing").table("test").filter(r.row[field] == current).update({field: new}).run()

	#retrieve an object in the database routing and table test
        def retrieve(self, host):
                doc = r.db("routing").table("test").filter(r.row["host"]==host).run()
                return doc
