#!/usr/bin/env python
import sys
sys.path.append('../changefeed')
sys.path.append('../rethink')
import rethinkdb as r
from tableManipulation import EditingLibrary
from changefeed import changes
import threading
import time
import subprocess

el = EditingLibrary()
changes = changes()
#connect = connect()

#changefeeds for testing purposes
class connect():
        #searches for new objects whose functions are compute
        def new_compute_object(self):
                r.connect("172.30.93.138",28015).repl()
                cursor = r.db("routing").table("test").changes().filter(lambda change: (change["old_val"] == None) and (change["new_val"]["function"]=="compute")).run()
                for change in cursor:
                        with open("pass.txt", "w") as testfile:
                                testfile.write(str(change))

        #searches for new objects whose functions are valor
        def new_valor_object(self):
                r.connect("172.30.93.138",28015).repl()
                cursor = r.db("routing").table("test").changes().filter(lambda change: (change["old_val"] == None) and (change["new_val"]["function"]=="valor")).run()
                for change in cursor:
                        with open("pass.txt", "w") as testfile:
                                testfile.write(str(change))

        #searches for new objects whose functions are unity
        def new_unity_object(self):
                r.connect("172.30.93.138",28015).repl()
                cursor = r.db("routing").table("test").changes().filter(lambda change: (change["old_val"] == None) and (change["new_val"]["function"]=="unity")).run()
                for change in cursor:
                        with open("pass.txt", "w") as testfile:
                                testfile.write(str(change))

connect = connect()

#test each part of the changefeed
def test_compute():
        open("pass.txt", "w").close()
        r.connect("172.30.93.138",28015).repl()
        t = threading.Thread(target=changes.main)
        t.daemon = True
        t.start()

        time.sleep(2)
        r.db("routing").table("galahad").insert([
                { "function": "compute", "address": "compute", "guestnet": "compute", "host": "compute"
                }
        ]).run()
        f = open("pass.txt", "r")
        content = f.read()
        f.close
        assert content != ""
        r.db("routing").table("galahad").filter(r.row["host"]=="compute").delete().run()

def test_valor():
        open("pass.txt", "w").close()
        r.connect("172.30.93.138",28015).repl()
        t = threading.Thread(target=changes.main)
        t.daemon = True
        t.start()

        time.sleep(2)
        r.db("routing").table("galahad").insert([
                { "function": "unity", "address": "unity", "guestnet": "unity", "host": "unity"
                }
        ]).run()
        f = open("pass.txt", "r")
        content = f.read()
        f.close
        assert content != ""
        r.db("routing").table("galahad").filter(r.row["host"]=="unity").delete().run()

def test_unity():
        open("pass.txt", "w").close()
        r.connect("172.30.93.138",28015).repl()
        t = threading.Thread(target=changes.main)
        t.daemon = True
        t.start()

        time.sleep(2)
        r.db("routing").table("galahad").insert([
                { "function": "valor", "address": "test172.30.87.97", "guestnet": "valor", "host": "valor"
                }
        ]).run()
        f = open("pass.txt", "r")
        content = f.read()
        f.close
        assert content != ""
        r.db("routing").table("galahad").filter(r.row["host"]=="valor").delete().run()

#reset table
def test_restart():
        r.db("routing").table("test").delete().run()
        r.db("routing").table("test").insert([
                { "function": "compute", "address": "172.30.126.211", "guestnet": "10.91.0.24", "host": "i-blablabla"
                }
        ]).run()

#test the compute part of the insert function in tableManipulation
def test_insert_compute():
        open("pass.txt", "w").close()
        t = threading.Thread(target=connect.new_compute_object)
        t.daemon = True
        t.start()
        time.sleep(1)
        el.insert("compute","test","test","compute_test")
        f = open("pass.txt", "r")
        content = f.read()
        print content
        f.close
        assert content != ""
        r.db("routing").table("test").filter(r.row["host"]=="compute_test").delete().run()

#test the compute part of the insert function in tableManipulation
def test_insert_valor():
        open("pass.txt", "w").close()
        t = threading.Thread(target=connect.new_valor_object)
        t.daemon = True
        t.start()
        time.sleep(1)
        el.insert("valor","test","test","valor_test")
        f = open("pass.txt", "r")
        content = f.read()
        print content
        f.close
        assert content != ""
        r.db("routing").table("test").filter(r.row["host"]=="valor_test").delete().run()

#tests the insert part of the insert function in tableManipulation
def test_insert_unity():
        open("pass.txt", "w").close()
        t = threading.Thread(target=connect.new_unity_object)
        t.daemon = True
        t.start()
        time.sleep(1)
        el.insert("unity","test","test","unity_test")
        f = open("pass.txt", "r")
        content = f.read()
        f.close
        assert content != ""
        r.db("routing").table("test").filter(r.row["host"]=="unity_test").delete().run()

#tests the insert function in tableManipulation
def test_insert_else():
        el.insert("z","x","c","v")
        doc = r.db("routing").table("test").filter(r.row["host"]=="v").run().next()
        countfinsert = r.db("routing").table("test").filter(r.row["host"]=="v").count().run()
        assert countfinsert == 1
        assert doc["function"] == "z"
        assert doc["address"] == "x"
        assert doc["guestnet"] == "c"
        assert doc["host"] == "v"
        r.db("routing").table("test").filter(r.row["host"]=="v").delete().run()

#tests the delete function in tableManipulation
def verify_delete():
        el.insert("a","b","c","d")
        el.delete("host","d")
        doc = r.db("routing").table("test").filter(r.row["host"]=="d").run()
        try:
                doc.next()
                return True
        except:
                return False

def test_delete():
        countfdelete = r.db("routing").table("test").filter(r.row["host"]=="d").count().run()
        assert countfdelete == 0
        assert verify_delete() == False
