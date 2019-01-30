import logging
import socket
import threading
import time

import rethinkdb as r

from __init__ import RT_DB, RT_IP, RT_PORT, RT_CERT
from __init__ import RT_VALOR_TB, RT_COMM_TB
from introspect_client import Introspect
from virtue_client import Virtue

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
        valor = r.db(RT_DB).table(RT_VALOR_TB).filter(
            {"function": "valor", "address": self.ip}).run(self.rt).next()
        self.valor_id = valor["valor_id"]
        self.valor_guestnet = valor["guestnet"]


    def run(self):
        if self.name == "valor":
            self.valor()    
        elif self.name == "migration":
            self.migration()

    def valor(self):
        for change in self.feed:
            rethinkdb_client_logger.debug(
                'Detected change feed in Valor: \n{}\n'.format(change))
            # For an change feed type of 'add'
            if change["type"] == "add" and change['new_val']['address'] == self.ip:
                self.add(change["new_val"])
            # For an change feed type of 'remove'
            elif change["type"] == "remove" and change['old_val']['address'] == self.ip:
                self.remove(change["old_val"])

    def add(self, change):
        virtue = Virtue(change)
        virtue.create_cfg(self.valor_guestnet)
        virtue.createDomU()

    def remove(self, change):
        virtue = Virtue(change)
        virtue.destroyDomU()

    def migrate(self, change):
        rethinkdb_client_logger.debug("MIGRATION - change = {}".format(change))
        rethinkdb_client_logger.debug("MIGRATION - table = {}".format(r.db(RT_DB).table(RT_VALOR_TB)\
            .run(self.rt)))

        virtue_dict = r.db(RT_DB).table(RT_VALOR_TB).filter({"virtue_id": change["virtue_id"]})\
            .run(self.rt).next()
        virtue = Virtue(virtue_dict)
        virtue.migrateDomU(change["valor_dest"])

        valor_dest = r.db(RT_DB).table(RT_VALOR_TB).filter({"function": "valor",
            "address": change["valor_dest"]}).run(self.rt).next()

        # history is already contained in the change feed.
        #history = r.db(RT_DB).table(RT_COMM_TB).filter({"virtue_id": virtue_id,
        #    "transducer_id": "migration"}).run(self.rt).next()["history"]
        history = change['history']
        history.append({"valor_id": self.valor_id})

        ### RethinkDB updating with dict causes inconsistencies. This updates transducer object. Need to cleanup
        comm_tb_filter = r.db(RT_DB).table(RT_COMM_TB).filter({"transducer_id": change["transducer_id"],
            "virtue_id": virtue.virtue_id})
        record = comm_tb_filter.run(self.rt).next()
        record["enabled"] = False
        record["history"] = history
        record["valor_dest"] = None
        record["valor_ip"] = change["valor_dest"]
        comm_tb_filter.update(record).run(self.rt)

        ### Updates Virtue object with new Valor IP
        valor_tb_filter = r.db(RT_DB).table(RT_VALOR_TB).filter({"virtue_id": change["virtue_id"],
            "function": "virtue"})
        valor_tb_filter.update(
            {"address": change["valor_dest"],
             "valor_id": valor_dest["valor_id"]}).run(self.rt)

    def migration(self):
        for change in self.feed:
            if (change["type"] == "change") and change["new_val"]["enabled"] == True:
                rethinkdb_client_logger.debug("Migration changefeed, change =")
                rethinkdb_client_logger.debug("    change = {}".format(change))
                self.migrate(change["new_val"])

class Rethink():
    def __init__(self):
        rethinkdb_client_logger.debug("Starting to monitor changes in rethinkDB...")
        self.valor_rt = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)
        self.migration_rt = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)

        self.ip = socket.gethostbyname(socket.gethostname())
        self.valor_id = r.db(RT_DB).table(RT_VALOR_TB).filter({"function":"valor", "address": self.ip}).run(
            self.valor_rt).next()["valor_id"]

    def changes(self):

        #valor_rt = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)
        valor_rt = self.valor_rt
        valor_feed = r.db(RT_DB).table(RT_VALOR_TB).filter({"function": "virtue"}).changes(include_types=True).run(valor_rt)

        #migration_rt = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)
        migration_rt = self.migration_rt
        migration_feed = r.db(RT_DB).table(RT_COMM_TB).filter({
            "valor_ip": self.ip,
            "transducer_id": "migration"}).changes(include_types=True).run(migration_rt)

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
        introspection_feed = r.db(RT_DB).table(RT_COMM_TB).filter({"valor_id": self.valor_id, 
            "transducer_id": "introspection"}).changes(include_types=True).run(introspection_rt)
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
                introspection_thread.event.clear()

if __name__ == "__main__":
    rt = Rethink()
    rt.changes()

    # super hacky but it works for now
    while True:
        time.sleep(3600)
