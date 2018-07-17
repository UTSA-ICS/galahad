#!/usr/bin/python
import rethinkdb as r
r.connect("172.30.93.138",28015).repl()

r.db('routing').table('transducer').filter(r.row['transducerId']=='m2').update({'flag':'TRUE'}).run()
r.db('routing').table('transducer').filter(r.row['transducerId']=='m2').run()
r.db('routing').table('transducer').filter(r.row['transducerId']=='m2').update({'flag':'FALSE'}).run()
r.db('routing').table('transducer').filter(r.row['transducerId']=='m2').run()

#config = {'host':'nx.tx','newHost':'TestNode.x'}
#r.db("routing").table("transducer").insert({
#    "transducerId" : "m1",
#    "flag" : "FALSE",
#    "config": config,
#    "history" : []
#}).run()

#r.db("routing").table("transducer").filter(r.row["transducerId"]=="test").delete().run()
