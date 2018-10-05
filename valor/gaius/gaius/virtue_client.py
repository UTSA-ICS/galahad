import os
import subprocess

from __init__ import CFG_OUT


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
