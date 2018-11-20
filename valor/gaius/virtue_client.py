import base64
import logging
import os
import subprocess

from __init__ import CFG_OUT

VIRTUE_LOGFILE = "/var/log/gaius-virtue.log"
virtue_handler = logging.FileHandler(VIRTUE_LOGFILE)

virtue_logger = logging.getLogger('virtue_client')
virtue_logger.setLevel(logging.DEBUG)
virtue_logger.addHandler(virtue_handler)


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

        virtue_logger.debug("Writing config file to {}.cfg".format(CFG_OUT + self.virtue_id))
        cfg = open(CFG_OUT + self.virtue_id + ".cfg", "w+")
        cfg.write("bootloader='/usr/local/lib/xen/bin/pygrub\'\n")
        cfg.write("vcpus=1\n")
        cfg.write("memory=1024\n")
        cfg.write("disk=['file:/mnt/efs/" + self.img_path + ",xvda2,w']\n")
        cfg.write("name='" + self.virtue_id + "'\n")
        cfg.write("vif=['bridge=hello-br0']\n")
        cfg.write("on_poweroff='destroy'\n")
        cfg.write("on_reboot='restart'\n")
        cfg.write("on_crash='restart'\n")
        cfg.write('cmdline = "unity-net={0} nameserver=172.30.0.2"'.format(unity_net64.decode()))
        cfg.close()

    def createDomU(self):
        try:
            out = subprocess.check_output('xl create ' + CFG_OUT + self.virtue_id + '.cfg', stderr=subprocess.STDOUT,
                                          shell=True)
            virtue_logger.debug("Virtue domU created")
            virtue_logger.debug(out)
        except subprocess.CalledProcessError as e:
            virtue_logger.debug("Error: Virtue creation failed")
            virtue_logger.debug("The command issued was: [{}]".format(e.cmd))
            virtue_logger.debug("The error output is: [{}]".format(e.output))

    def migrateDomU(self, target_ip):
        try:
            out = subprocess.check_output(
                'xl migrate -s "ssh -o StrictHostKeyChecking=no" ' + self.virtue_id + ' ' + target_ip,
                stderr=subprocess.STDOUT, shell=True)
            virtue_logger.debug("Virtue migrated")
            virtue_logger.debug(out)
        except subprocess.CalledProcessError as e:
            virtue_logger.debug("Error: Virtue migration failed")
            virtue_logger.debug("The command issued was: [{}]".format(e.cmd))
            virtue_logger.debug("The error output is: [{}]".format(e.output))

    def destroyDomU(self):
        try:
            os.remove(CFG_OUT + self.virtue_id + ".cfg")
        except:
            virtue_logger.debug("Error: {} not found".format(CFG_OUT + self.virtue_id + ".cfg"))

        try:
            # Needs to be in separate try statement because virtue may exist when .cfg doesn't
            out = subprocess.check_output('xl destroy ' + self.virtue_id, stderr=subprocess.STDOUT, shell=True)
            virtue_logger.debug(out)
        except subprocess.CalledProcessError as e:
            virtue_logger.debug("Error: Virtue destruction failed")
            virtue_logger.debug("The command issued was: [{}]".format(e.cmd))
            virtue_logger.debug("The error output is: [{}]".format(e.output))
