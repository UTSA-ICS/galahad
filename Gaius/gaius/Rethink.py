import rethinkdb as r
import socket

from __init__ import RT_CONN, RT_DB, RT_VALOR_TB, RT_TRANS_TB
from Virtue import Virtue

class Rethink():
    def __init__(self):
        self.ip = socket.gethostbyname(socket.gethostname())

    def printtable(self):
        print r.db(RT_DB).table(RT_VALOR_TB).run(RT_CONN)

    def changes_virtue(self):
        feed = r.db(RT_DB).table(RT_VALOR_TB).filter({'function':'virtue','address':self.ip}).changes().run(RT_CONN)
        for change in feed:
            if change['old_val'] is None:
                print('insert')
                virtue = Virtue(change['new_val'])
                virtue.create_cfg()
                virtue.createDomU()
            elif change['new_val'] is None:
                print('delete')
                virtue = Virtue(change['old_val'])
                virtue.destroyDomU()
            else:
                print('update')

if __name__ == "__main__":
    rt = Rethink()
    rt.changes_virtue()
