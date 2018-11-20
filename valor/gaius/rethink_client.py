import logging
import socket
import threading
import time

import rethinkdb as r
from __init__ import RT_DB, RT_IP, RT_PORT, RT_CERT
from __init__ import RT_VALOR_TB, RT_COMM_TB
from virtue_client import Virtue

RETHINKDB_LOGFILE = "/var/log/gaius-rethinkdb.log"
rethinkdb_handler = logging.FileHandler(RETHINKDB_LOGFILE)

rethinkdb_logger = logging.getLogger('rethinkdb_client')
rethinkdb_logger.setLevel(logging.DEBUG)
rethinkdb_logger.addHandler(rethinkdb_handler)


class Changes(threading.Thread):
    def __init__(self, name, feed, rt):
        rethinkdb_logger.debug("Starting Gaius Service to monitor rethinkDB for changes")

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
                rethinkdb_logger.debug("Valor changefeed, change type = add")
                self.add(change["new_val"])
            elif change["type"] == "remove":
                rethinkdb_logger.debug("Valor changefeed, change type = remove")
                self.remove(change["old_val"])

    def getid(self, table, search):
        doc = r.db(RT_DB).table(table).filter(search).run(self.rt)
        return doc.next()["id"]

    def add(self, change):
        if change["function"] == "virtue":
            valor = r.db(RT_DB).table(RT_VALOR_TB).filter({"function": "valor", "address": self.ip}).run(self.rt).next()

            virtue = Virtue(change)
            virtue.create_cfg(valor["guestnet"])
            virtue.createDomU()
            comm = {
                "transducer_id": virtue.img_path,
                "virtue_id": self.getid(RT_VALOR_TB, {"virtue_id": virtue.virtue_id}),
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
            virtue = Virtue(change)
            virtue.destroyDomU()

    def migrate(self, change):
        virtue_dict = r.db(RT_DB).table(RT_VALOR_TB).filter({"id": change["virtue_id"]}).run(self.rt).next()
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
                rethinkdb_logger.debug("Migration changefeed, change =")
                rethinkdb_logger.debug("    change = {}".format(change))
                self.migrate(change["new_val"])

class Rethink():
    def __init__(self):
        rethinkdb_logger.debug("Starting to monitor changes in rethinkDB...")

        self.ip = socket.gethostbyname(socket.gethostname())

    def changes(self):

        valor_rt = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)
        valor_feed = r.db(RT_DB).table(RT_VALOR_TB).filter({"function": "virtue", "address": self.ip}).changes(include_types=True).run(valor_rt)

        migration_rt = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)
        migration_feed = r.db(RT_DB).table(RT_COMM_TB).filter({"valor_ip": self.ip, "type": "MIGRATION"}).changes(include_types=True).run(migration_rt)

        valor_thread = Changes("valor", valor_feed, valor_rt)
        valor_thread.daemon = True
        valor_thread.start()
        rethinkdb_logger.debug("Valor thread starting...")

        migration_thread = Changes("migration", migration_feed, migration_rt)
        migration_thread.daemon = True
        migration_thread.start()
        rethinkdb_logger.debug("Migration thread starting...")

if __name__ == "__main__":
    rt = Rethink()
    rt.changes()

    # super hacky but it works for now
    while True:
        time.sleep(3600)
