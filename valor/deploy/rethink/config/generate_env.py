import rethinkdb as r
r.connect("localhost", 28015).repl()

r.db_create('routing').run()
r.db('routing').table_create('galahad').run()
r.db('routing').table('galahad').insert([
	{ "host" 	: "i-04d0aaf3c6c86572f",
	  "function" 	: "router",
	  "address"	: "172.30.1.53",
	  "guestnet"	: "10.91.0.254" }]).run()
r.db('routing').table('galahad').insert([
	{ "host"	: "i-0416d64601be1edbd",
	  "function"	: "compute",
	  "address"	: "172.30.1.51",
	  "guestnet"	: "10.91.0.1" }]).run()
r.db('routing').table('galahad').insert([
	{ "host"	: "i-0a95cbd2d8f37c8a7",
	  "function"	: "compute",
	  "address"	: "172.30.1.52",
	  "guestnet"	: "10.91.0.2" }]).run()
