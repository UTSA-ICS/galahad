import rethinkdb as r
import socket
import datetime
import time
import threading

from __init__ import RT_CONN, RT_DB, RT_IP, RT_PORT, RT_CERT
from __init__ import RT_VALOR_TB, RT_COMM_TB, RT_ACK_TB, RT_ARC_TB
from Virtue import Virtue

class Changes(threading.Thread):
    def __init__(self, name, feed, rt):
        print("Changes __init__")
        threading.Thread.__init__(self)
        self.feed = feed
        self.ip = socket.gethostbyname(socket.gethostname())
        self.name = name
        self.rt = rt

    def run(self):
        print("Changes run")
        if self.name == "valor":
            print("self.name == 'valor'")
            self.valor()    
        elif self.name == "migration":
            print("self.name == 'migration'")
            self.migration()

    def valor(self):
        print("Changes valor\r")
        for change in self.feed:
            if change["type"] == "add":
                print("change['type'] == 'add'\r")
                self.add(change["new_val"])
            elif change["type"] == "remove":
                print("change['type'] == 'remove'\r")
                self.remove(change["old_val"])

    def getid(self, table, search):
        doc = r.db(RT_DB).table(table).filter(search).run(self.rt)
        return doc.next()["id"]

    def add(self, change):
        print("Changes add")
        if change["function"] == "virtue":
            virtue = Virtue(change)
            virtue.create_cfg()
            virtue.createDomU()
            comm = {
                "transducer_id": virtue.img_path,
                "virtue_id": self.getid(RT_VALOR_TB, {"host": virtue.host}),
                "valor_ip": self.ip,
                "enabled": False,
                "type": "MIGRATION",
                "history": [{
                    "valor": self.getid(RT_VALOR_TB, {"function": "valor", "address": self.ip})}]
            }
            r.db(RT_DB).table(RT_COMM_TB).insert(comm).run(self.rt)
            print("Virtue transducer object added to commands table")
            print("Commands table = {}".format(r.db(RT_DB).table(RT_COMM_TB).run(self.rt)))

    def remove(self, change):
        print("Changes remove")
        if change["function"] == "virtue":
            virtue = Virtue(change)
            virtue.destroyDomU()
            print("Virtue DomU destroyed")

    def migrate(self, change):
        print("Changes migrate")
        r.db(RT_DB).table(RT_COMM_TB).filter({change["valor_ip"]==self.ip}).update({"enabled": False}).run(self.rt)

    def migration(self):
        print("Changes migration")
        for change in self.feed:
            print("change")
            if (change["type"] == "change") and change["new_val"]["enabled"]:
                self.migrate(change["new_val"])

class Rethink():
    def __init__(self):
        self.ip = socket.gethostbyname(socket.gethostname())

    def printtable(self):
        print r.db(RT_DB).table(RT_VALOR_TB).run(self.rt)

    def changes_valor(self, feed):
        for change in feed:
            if change['type'] == 'add':
                print("change['type'] == 'add'")
                self.add(change['new_val'])
            elif change['type'] == 'remove':
                print("change['type'] == 'remove'")
                self.remove(change['old_val'])

    def changes(self):
        print("Entered changes")

        valor_rt = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)
        valor_feed = r.db(RT_DB).table(RT_VALOR_TB).filter({"function": "virtue", "address": self.ip}).changes(include_types=True).run(valor_rt)

        migration_rt = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)
        migration_feed = r.db(RT_DB).table(RT_COMM_TB).filter({"valor_ip": self.ip, "type": "MIGRATION"}).changes(include_types=True).run(migration_rt)

        #valor_feed = r.db(RT_DB).table(RT_VALOR_TB).changes(include_types=True).run(RT_CONN)
        #migration_feed = r.db(RT_DB).table(RT_VALOR_TB).changes(include_types=True).run(RT_CONN)

        valor_thread = Changes("valor", valor_feed, valor_rt)
        valor_thread.daemon = True
        valor_thread.start()
        print("Valor thread started")

        migration_thread = Changes("migration", migration_feed, migration_rt)
        migration_thread.daemon = True
        migration_thread.start()
        print("Migration thread started")

        time.sleep(360)


if __name__ == "__main__":
    rt = Rethink()
    rt.changes()
