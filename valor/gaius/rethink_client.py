# Copyright (c) 2019 by Star Lab Corp.

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
        rethinkdb_client_logger.debug(
            "Starting Gaius Service to monitor rethinkDB for changes")

        threading.Thread.__init__(self)
        self.feed = feed
        self.ip = socket.gethostbyname(socket.gethostname())
        self.name = name
        self.rt = rt
        valor = r.db(RT_DB).table(RT_VALOR_TB).filter(
            {"function": "valor", "address": self.ip}).run(self.rt).next()
        self.valor_id = valor["valor_id"]
        self.valor_guestnet = valor["guestnet"]
        self.introspection_threads = []

    def run(self):
        if self.name == "valor":
            self.valor()
        elif self.name == "migration":
            self.migration()
        elif self.name == "introspection":
            self.introspection()

    def valor(self):
        for change in self.feed:
            # For an change feed type of 'add'
            if change["type"] == "add" and change['new_val']['address'] == self.ip:
                self.add(change["new_val"])
            # For an change feed type of 'remove'
            elif change["type"] == "remove" and change['old_val']['address'] == self.ip:
                self.remove(change["old_val"])

    def add(self, change):
        rethinkdb_client_logger.debug(
            'Detected ADD change feed in Valor: \n{}\n'.format(change))
        virtue = Virtue(change)
        virtue.create_cfg(self.valor_guestnet)
        virtue.createDomU()

    def remove(self, change):
        rethinkdb_client_logger.debug(
            'Detected REMOVE change feed in Valor: \n{}\n'.format(change))
        virtue = Virtue(change)
        virtue.destroyDomU()

    def migrate(self, change):
        rethinkdb_client_logger.debug("MIGRATION - change = {}".format(change))

        virtue_dict = r.db(RT_DB).table(RT_VALOR_TB).filter(
            {"virtue_id": change["virtue_id"]}).run(self.rt).next()
        virtue = Virtue(virtue_dict)
        virtue.migrateDomU(change["valor_dest"])

        valor_dest = r.db(RT_DB).table(RT_VALOR_TB).filter({"function": "valor",
                                                            "address": change["valor_dest"]}).run(self.rt).next()

        history = change['history']
        history.append({"valor_id": self.valor_id})

        # RethinkDB updating with dict causes inconsistencies. This updates
        # transducer object. Need to cleanup
        comm_tb_filter = r.db(RT_DB).table(RT_COMM_TB).filter(
            {"transducer_id": change["transducer_id"], "virtue_id": virtue.virtue_id})
        record = comm_tb_filter.run(self.rt).next()
        record["enabled"] = False
        record["history"] = history
        record["valor_dest"] = None
        record["valor_ip"] = change["valor_dest"]
        comm_tb_filter.update(record).run(self.rt)

        # Updates Virtue object with new Valor IP
        valor_tb_filter = r.db(RT_DB).table(RT_VALOR_TB).filter(
            {"virtue_id": change["virtue_id"], "function": "virtue"})
        valor_tb_filter.update(
            {"address": change["valor_dest"],
             "valor_id": valor_dest["valor_id"]}).run(self.rt)

    def migration(self):
        for change in self.feed:
            if (change["type"] == "change") and change["new_val"]["enabled"] is True:
                rethinkdb_client_logger.debug("Migration changefeed, change =")
                rethinkdb_client_logger.debug("    change = {}".format(change))
                self.migrate(change["new_val"])

    def introspection(self):
        for change in self.feed:
            rethinkdb_client_logger.debug(
                "Introspection change feed detected: {}".format(change))
            if change["type"] == "add":
                if change["new_val"]["enabled"] is True:
                    self.introspection_add(change["new_val"])
                else:
                    # Do nothing as this is the initial virtue entry in rethinkdb with
                    # introspection disabled.
                    pass
            elif change["type"] == "remove":
                self.introspection_remove(change)
            elif change["type"] == "change":
                self.introspection_change(change)

    def get_virtue_introspection_thread(self, virtue_id):
        for thread in self.introspection_threads:
            if thread.virtue_id == virtue_id:
                return thread
        return

    def introspection_add(self, change):
        introspection_thread = Introspect(change["virtue_id"],
                                          change["comms"],
                                          change["interval"])
        introspection_thread.start()
        self.introspection_threads.append(introspection_thread)

    def introspection_remove(self, change):
        introspection_thread = self.get_virtue_introspection_thread(change["virtue_id"])
        if introspection_thread:
            introspection_thread.stop_introspect()
            self.introspection_threads.remove(introspection_thread)

    def introspection_change(self, change):
        # Update if introspection is enabled
        if change["old_val"]["enabled"] is False and change["new_val"]["enabled"] is True:
            self.introspection_add(change["new_val"])

        # Update if introspection is disabled
        elif change["old_val"]["enabled"] is True and change["new_val"]["enabled"] is False:
            self.introspection_remove(change["new_val"])

        # Update if introspection was enabled but its parameters changed.
        elif change["old_val"]["enabled"] is True and change["new_val"]["enabled"] is True:
            introspection_thread = self.get_virtue_introspection_thread(
                change["new_val"]["virtue_id"])
            if introspection_thread:
                # Update if interval changes
                if change["old_val"]["interval"] is not change["new_val"]["interval"]:
                    introspection_thread.set_interval(change["new_val"]["interval"])
                # Update if the list of modules changes
                if change["old_val"]["comms"] is not change["new_val"]["comms"]:
                    introspection_thread.set_comms(change["new_val"]["comms"])


class Rethink():
    def __init__(self):
        rethinkdb_client_logger.debug("Starting to monitor changes in rethinkDB...")
        self.valor_rt = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)
        self.migration_rt = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)
        self.introspection_rt = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)

        self.ip = socket.gethostbyname(socket.gethostname())
        self.valor_id = r.db(RT_DB).table(RT_VALOR_TB).filter(
            {"function": "valor", "address": self.ip}).run(self.valor_rt).next()["valor_id"]

    def changes(self):
        # Virtue updates
        # Handle changes related to the galahad table for the virtue
        valor_feed = r.db(RT_DB).table(RT_VALOR_TB).filter(
            {"function": "virtue"}).changes(include_types=True).run(self.valor_rt)

        valor_thread = Changes("valor", valor_feed, self.valor_rt)
        valor_thread.daemon = True
        valor_thread.start()
        rethinkdb_client_logger.debug("Valor thread starting...")

        # Migration updates
        # Handle changes related to the transducer table for migration
        migration_feed = r.db(RT_DB).table(RT_COMM_TB).filter(
            {"valor_ip": self.ip, "transducer_id": "migration"}).changes(
            include_types=True).run(self.migration_rt)

        migration_thread = Changes("migration", migration_feed, self.migration_rt)
        migration_thread.daemon = True
        migration_thread.start()
        rethinkdb_client_logger.debug("Migration thread starting...")

        # Introspection updates
        # Handle changes related to the transducer table for introspection
        introspection_feed = r.db(RT_DB).table(RT_COMM_TB).filter(
            {"valor_id": self.valor_id, "transducer_id": "introspection"}).changes(
            include_types=True).run(self.introspection_rt)

        introspection_thread = Changes("introspection", introspection_feed,
                                       self.introspection_rt)
        introspection_thread.daemon = True
        introspection_thread.start()
        rethinkdb_client_logger.debug("Introspection thread starting...")


if __name__ == "__main__":
    rt = Rethink()
    rt.changes()

    # while loop to keep the program alive/running
    while True:
        time.sleep(3600)
