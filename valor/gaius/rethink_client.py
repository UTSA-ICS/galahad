import rethinkdb as r
import socket
import datetime
import time
import threading
import base64
import logging

from __init__ import RT_CONN, RT_DB, RT_IP, RT_PORT, RT_CERT
from __init__ import RT_VALOR_TB, RT_COMM_TB, RT_ACK_TB, RT_ARC_TB
from virtue_client import Virtue
from introspect_client import Introspect

RETHINKDB_LOGFILE = "/var/log/gaius-rethink.log"
rethinkdb_client_handler = logging.FileHandler(RETHINKDB_LOGFILE)
rethinkdb_client_logger = logging.getLogger('rethinkdb')
rethinkdb_client_logger.setLevel(logging.DEBUG)
rethinkdb_client_logger.addHandler(rethinkdb_client_handler)

class Changes(threading.Thread):
    def __init__(self, name, feed, rt):
        rethinkdb_client_logger.debug("Starting Gaius Service to monitor rethinkDB for changes")

        threading.Thread.__init__(self)
        self.feed = feed
        self.ip = socket.gethostbyname(socket.gethostname())
        self.name = name
        self.rt = rt

    def run(self):
        if self.name == "valor":
            self.valor()    
        elif self.name == "migration":
            self.migration()

    def valor(self):
        for change in self.feed:
            if change["type"] == "add":
                self.add(change["new_val"])
            elif change["type"] == "remove":
                self.remove(change["old_val"])

    def getid(self, table, search):
        doc = r.db(RT_DB).table(table).filter(search).run(self.rt)
        return doc.next()["id"]

    def add(self, change):
        if change["function"] == "virtue":
            valor = r.db(RT_DB).table(RT_VALOR_TB).filter({"function": "valor", "address": self.ip}).run(self.rt).next()

            virtue = Virtue(change)
            try:
                r.db(RT_DB).table(RT_COMM_TB).filter({"virtue_id": virtue.virtue_id}).update({"enabled":"False"}).run(self.rt).next()
                return
            except Exception as e:
                pass

            rethinkdb_client_logger.debug("Continuing...")
            virtue.create_cfg(valor["guestnet"])
            virtue.createDomU()
            comm = {
                "transducer_id": virtue.img_path,
                "virtue_id": virtue.virtue_id,
                "valor_ip": self.ip,
                "valor_dest": None,
                "enabled": False,
                "type": "MIGRATION",
                "history": [{
                    "valor": self.getid(RT_VALOR_TB, {"function": "valor", "address": self.ip})}]
            }
            r.db(RT_DB).table(RT_COMM_TB).insert(comm).run(self.rt)

    def remove(self, change):
        if change["function"] == "virtue":
            rethinkdb_client_logger.debug("Valor remove change = {}".format(change))
            virtue = Virtue(change)
            r.db(RT_DB).table(RT_COMM_TB).filter({"virtue_id": virtue.virtue_id}).delete().run(self.rt)
            virtue.destroyDomU()

    def migrate(self, change):
        rethinkdb_client_logger.debug("MIGRATION - change = {}".format(change))
        rethinkdb_client_logger.debug("MIGRATION - table = {}".format(r.db(RT_DB).table(RT_VALOR_TB).run(self.rt)))
        virtue_dict = r.db(RT_DB).table(RT_VALOR_TB).filter({"virtue_id": change["virtue_id"]}).run(self.rt).next()
        virtue = Virtue(virtue_dict)
        virtue.migrateDomU(change["valor_dest"])
        valor_dest = r.db(RT_DB).table(RT_VALOR_TB).filter({"function": "valor", "address": change["valor_dest"]}).run(self.rt).next()
        history = r.db(RT_DB).table(RT_COMM_TB).filter({"virtue_id": change["virtue_id"]}).run(self.rt).next()["history"]
        history.append({"valor": self.getid(RT_VALOR_TB, {"function": "valor", "address": self.ip})})

        ### RethinkDB updating with dict causes inconsistencies. This updates transducer object. Need to cleanup
        r.db(RT_DB).table(RT_COMM_TB).filter({"transducer_id": change["transducer_id"]}).update({"enabled": False}).run(self.rt)
        r.db(RT_DB).table(RT_COMM_TB).filter({"transducer_id": change["transducer_id"]}).update({"valor_ip": change["valor_dest"]}).run(self.rt)
        r.db(RT_DB).table(RT_COMM_TB).filter({"transducer_id": change["transducer_id"]}).update({"valor_dest": None}).run(self.rt)
        r.db(RT_DB).table(RT_COMM_TB).filter({"transducer_id": change["transducer_id"]}).update({"history": history}).run(self.rt)

        ### Updates Virtue object with new Valor IP
        r.db(RT_DB).table(RT_VALOR_TB).filter({"id": change["virtue_id"]}).update({"address": change["valor_dest"]}).run(self.rt)

    def migration(self):
        for change in self.feed:
            if (change["type"] == "change") and change["new_val"]["enabled"]:
                rethinkdb_client_logger.debug("Migration changefeed, change =")
                rethinkdb_client_logger.debug("    change = {}".format(change))
                self.migrate(change["new_val"])

class Rethink():
    def __init__(self):
        rethinkdb_client_logger.debug("Starting to monitor changes in rethinkDB...")

        self.ip = socket.gethostbyname(socket.gethostname())

    def changes(self):

        valor_rt = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)
        valor_feed = r.db(RT_DB).table(RT_VALOR_TB).filter({"function": "virtue", "address": self.ip}).changes(include_types=True).run(valor_rt)

        migration_rt = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)
        migration_feed = r.db(RT_DB).table(RT_COMM_TB).filter({"valor_ip": self.ip, "type": "MIGRATION"}).changes(include_types=True).run(migration_rt)

        valor_thread = Changes("valor", valor_feed, valor_rt)
        valor_thread.daemon = True
        valor_thread.start()
        rethinkdb_client_logger.debug("Valor thread starting...")

        migration_thread = Changes("migration", migration_feed, migration_rt)
        migration_thread.daemon = True
        migration_thread.start()
        rethinkdb_client_logger.debug("Migration thread starting...")

        introspection_thread = Introspect()
        introspection_thread.start()
        introspection_rt = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)
        introspection_feed = r.db(RT_DB).table(RT_COMM_TB).filter({"valor_id": self.ip, "type": "INTROSPECTION"}).changes(include_types=True).run(introspection_rt)
        for change in introspection_feed:
            rethinkdb_client_logger.debug(change)
            if change["type"] == "add":
                introspection_thread.set_virtue_id(change["new_val"]["virtue_id"])
                introspection_thread.set_interval(change["new_val"]["interval"])
                introspection_thread.set_comms(change["new_val"]["comms"])
            elif change["type"] == "change":
                if change["old_val"]["virtue_id"] is not change["new_val"]["virtue_id"]:
                    introspection_thread.set_virtue_id(change["new_val"]["virtue_id"])
                    rethinkdb_client_logger.debug("changed = virtue_id")
                if change["old_val"]["interval"] is not change["new_val"]["interval"]:
                    introspection_thread.set_interval(change["new_val"]["interval"])
                    rethinkdb_client_logger.debug("changed = interval")
                if change["old_val"]["comms"] is not change["new_val"]["comms"]:
                    introspection_thread.set_comms(change["new_val"]["comms"])
                    rethinkdb_client_logger.debug("changed = comms")
                if change["old_val"]["enabled"] == False and change["new_val"]["enabled"] == True:
                    introspection_thread.event.set()
                    rethinkdb_client_logger.debug("introspection_thread.event.set()")
                elif change["old_val"]["enabled"] == True and change["new_val"]["enabled"] == False:
                    introspection_thread.event.clear()
                    rethinkdb_client_logger.debug("introspection_thread.event.clear()")
            elif change["type"] == "remove":
                introspection_thread.clear()

if __name__ == "__main__":
    rt = Rethink()
    rt.changes()

    # super hacky but it works for now
    while True:
        time.sleep(3600)
