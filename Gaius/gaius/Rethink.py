import rethinkdb as r
import socket
import datetime

from __init__ import RT_CONN, RT_DB
from __init__ import RT_VALOR_TB, RT_COMM_TB, RT_ACK_TB, RT_ARC_TB
from Virtue import Virtue

class Rethink():
    def __init__(self):
        self.ip = socket.gethostbyname(socket.gethostname())

    def printtable(self):
        print r.db(RT_DB).table(RT_VALOR_TB).run(RT_CONN)

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
                    'valor': self.getid(RT_VALOR_TB, {'function':'valor', 'address': self.ip}),
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
            print "migrate"
        elif 'enabled' in change and change['enabled'] == False:
            ### confirm migration - ack response added 

    def changes(self):
        feed = r.db(RT_DB).table(RT_VALOR_TB).union(r.db(RT_DB).table(RT_COMM_TB)).filter({'address': self.ip}).changes(include_types=True).run(RT_CONN)

        for change in feed:
            if change['type'] == 'add':
                self.add(change['new_val']
            if change['type'] == 'remove':
                self.remove(change['old_val'])
            if change['type'] == 'change':
                print "update"

        """
            elif change['new_val'] is None:
                print('delete')
                virtue = Virtue(change['old_val'])
                virtue.destroyDomU()
            else:
                print('update')
        """
                

if __name__ == "__main__":
    rt = Rethink()
    rt.changes()
