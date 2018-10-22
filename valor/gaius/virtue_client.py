import os, subprocess
import logging
import base64
from __init__ import CFG_OUT

GAIUS_LOGFILE = "/var/log/gaius-virtue.log"
logging.basicConfig(filename=GAIUS_LOGFILE, level=logging.DEBUG)

class Virtue():
    def __init__(self, v_dict):
        self.virtue_id = v_dict['virtue_id']
        self.address = v_dict['address']
        self.guestnet = v_dict['guestnet']
        self.img_path = v_dict['img_path']

    def create_cfg(self, valor_guestnet):
        unity_net = ('ip add add {0}/24 dev eth0;ip link set dev eth0 up;'
                     'ip route add default via {1} dev eth0').format(self.guestnet, valor_guestnet)
        unity_net64 = base64.b64encode(unity_net.encode())

        logging.debug("Writing config file to {}.cfg".format(CFG_OUT + self.virtue_id))
        cfg = open(CFG_OUT + self.virtue_id + ".cfg", "w+")
        cfg.write("bootloader='/usr/local/lib/xen/bin/pygrub\'\n")
        cfg.write("vcpus=1\n")
        cfg.write("memory=1024\n")
        cfg.write("disk=['file:" + self.img_path + ",xvda2,w']\n")
        cfg.write("name='" + self.virtue_id + "'\n")
        cfg.write("vif=['bridge=hello-br0']\n")
        cfg.write("on_poweroff='destroy'\n")
        cfg.write("on_reboot='restart'\n")
        cfg.write("on_crash='restart'\n")
        cfg.write('cmdline = "unity-net={0} nameserver=1.1.1.1"'.format(unity_net64.decode()))
        cfg.close()

    def createDomU(self):
        try:
            subprocess.check_call(['xl','create',CFG_OUT + self.virtue_id + '.cfg'])
            print("Virtue() domU created")
        except:
            print("Error: Virtue creation failed")

    def migrateDomU(self, target_ip):
        try:
            subprocess.check_call(['xl','migrate', self.virtue_id, target_ip])
            print("Virtue() migrated")
        except:
            print("Error: Virtue migration failed") 

    def destroyDomU(self):
        try:
            os.remove(CFG_OUT + self.virtue_id + ".cfg")
        except:
            print("Error: {} not found".format(CFG_OUT + self.virtue_id + ".cfg"))

        try:
            # Needs to be in separate try statement because virtue may exist when .cfg doesn't
            subprocess.check_call(['xl','destroy', self.virtue_id])
        except:
            print("Error: Virtue destruction failed")
