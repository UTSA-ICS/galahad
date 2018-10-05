#!/usr/bin/env python

import datetime
import os
import socket
import subprocess

import rethinkdb as r

RT_HOSTNAME = "rethinkdb.galahad.com"
RT_PORT = 28015
RETHINKDB_CERT = '/mnt/efs/galahad-keys/rethinkdb_cert.pem'

RT_CONN = r.connect(
    host=RT_HOSTNAME,
    port=RT_PORT,
    ssl={
        'ca_certs': RETHINKDB_CERT
    })

RT_DB = "transducers"
RT_VALOR_TB = "galahad"
RT_TRANS_TB = "transducer"
RT_COMM_TB = "commands"
RT_ACK_TB = "acks"
RT_ARC_TB = "archive"

CFG_OUT = "./cfg/"


class RethinkDB():

    def __init__(self):
        self.ip = socket.gethostbyname(socket.gethostname())

    def printtable(self):
        print
        r.db(RT_DB).table(RT_VALOR_TB).run(RT_CONN)

    def getid(self, table, search):

        doc = r.db(RT_DB).table(table).filter(search).run(RT_CONN)

        return doc.next()['id']

    def add(self, change):

        if 'function' in change and change['function'] == 'virtue':
            virtue = Virtue(change)
            virtue.create_cfg()
            virtue.createDomU()
            comm = {
                'transducer_id': virtue.img_path,
                'virtue_id': self.getid(RT_VALOR_TB, {'host': virtue.host}),
                'enabled': False,
                'configuration': None,
                'type': 'MIGRATION',
                'history': [{
                    'valor': self.getid(
                        RT_VALOR_TB,
                        {
                            'function': 'valor',
                            'address': self.ip
                        }),
                    'timestamp': str(datetime.datetime.now())}]
            }

            r.db(RT_DB).table(RT_COMM_TB).insert(comm).run(RT_CONN)

    def remove(self, change):
        if 'function' in change and change['function'] == 'virtue':
            virtue = Virtue(change)
            virtue.destroyDomU()
            ### add transducer update

    def update(self, change):
        if 'enabled' in change and change['enabled'] == True:
            ### perform migration
            print
            "migrate"
        elif 'enabled' in change and change['enabled'] == False:
            ### confirm migration - ack response added
            print
            "confirm migration"

    def changes(self):
        feed = r.db(RT_DB).table(RT_VALOR_TB).union(r.db(RT_DB).table(RT_COMM_TB)).filter({'address': self.ip}).changes(
            include_types=True).run(RT_CONN)

        for change in feed:
            if change['type'] == 'add':
                self.add(change['new_val'])
            if change['type'] == 'remove':
                self.remove(change['old_val'])
            if change['type'] == 'change':
                print
                "update"

        """
            elif change['new_val'] is None:
                print('delete')
                virtue = Virtue(change['old_val'])
                virtue.destroyDomU()
            else:
                print('update')
        """


class Virtue():
    def __init__(self, v_dict):
        self.host = v_dict['host']
        self.address = v_dict['address']
        self.guestnet = v_dict['guestnet']
        self.img_path = v_dict['img_path']

    def create_cfg(self):
        cfg = open(CFG_OUT + self.host + ".cfg", "w+")
        cfg.write("bootloader='/usr/local/lib/xen/bin/pygrub\'\n")
        cfg.write("vcpus=1\n")
        cfg.write("memory=1024\n")
        cfg.write("disk=['file:" + self.img_path + ",xvda2,w']\n")
        cfg.write("name='" + self.host + "'\n")
        cfg.write("vif=['bridge=hello-br0']\n")
        cfg.write("on_poweroff='destroy'\n")
        cfg.write("on_reboot='restart'\n")
        cfg.write("on_crash='restart'\n")
        cfg.write("extra=\"ip=" + self.guestnet + "::" + self.address + ":255.255.255.0:host:eth0:none " + \
                  "nameserver=1.1.1.1\"")
        cfg.close()

    def createDomU(self):
        subprocess.check_call(['xl', 'create', CFG_OUT + self.host + '.cfg'])

    def destroyDomU(self):
        os.remove(CFG_OUT + self.host + ".cfg")
        subprocess.check_call(['xl', 'destroy', self.host])


if __name__ == "__main__":
    rt = RethinkDB()
    rt.changes()
