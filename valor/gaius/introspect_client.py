import logging
import subprocess
import time
import datetime
import threading
import shutil

INTRO_LOGFILE = "/var/log/gaius-introspect.log"
intro_handler = logging.FileHandler(INTRO_LOGFILE)

intro_logger = logging.getLogger('introspect-client')
intro_logger.setLevel(logging.DEBUG)
intro_logger.addHandler(intro_handler)

class Introspect(threading.Thread):
    def __init__(self):
        self.virtue_id = None
        self.interval = None
        self.comms = []
        threading.Thread.__init__(self)
        self.event = threading.Event()
        self.event.clear()

    def run(self):
        print("run()")
        while True:
            print("Entered while stmt")
            intro_logger.debug("Entered while stmt: {}".format(datetime.datetime.now()))
            self.event.wait()
            for comm in self.comms:
                getattr(self, comm)()
            time.sleep(self.interval)

    def set_virtue_id(self, virtue_id): 
        self.virtue_id = virtue_id
        contents = []
        f = open("/etc/libvmi.conf")
        for line in f.readlines():
            contents.append(line)
        f.close()
        intro_logger.debug(contents)
        contents[0] = self.virtue_id + " {\n"
        intro_logger.debug(contents)
        f_new = open("/etc/libvmi.conf", "w")
        for line in contents:
            f_new.write(line)
        f.close()

    def set_interval(self, interval):
        self.interval = interval

    def set_comms(self, comms):
        self.comms = comms

    def enable(self, comm):
        self.comms.append(comm)

    def disable(self, comm):
        self.comms.remove(comm)

    def process_list(self):
        try:
            out = subprocess.check_output("echo \"process-list {}\" | nc -U /tmp/control.socket".format(self.virtue_id), stderr=subprocess.STDOUT, shell=True)
            intro_logger.debug("process-list {}: {}".format(self.virtue_id, out))
        except subprocess.CalledProcessError as e:
            intro_logger.debug("process-list {}: {}".format(self.virtue_id, e))

    def kernel_modules(self):
        try:
            out = subprocess.check_output("echo \"kernel-modules {}\" | nc -U /tmp/control.socket".format(self.virtue_id), stderr=subprocess.STDOUT, shell=True)
            intro_logger.debug("kernel-modules {}: {}".format(self.virtue_id, out))
        except subprocess.CalledProcessError as e:
            intro_logger.debug("kernel-modules {}: {}".format(self.virtue_id, e))

    def inspect_virtue_lsm(self):
        try:
            out = subprocess.check_output("echo \"inspect-virtue-lsm {}\" | nc -U /tmp/control.socket"\
                .format(self.virtue_id), stderr=subprocess.STDOUT, shell=True)
            intro_logger.debug("inspect-virtue-lsm {}: {}".format(self.virtue_id, out))
        except subprocess.CalledProcessError as e:
            intro_logger.debug("inspect-virtue-lsm {}: {}".format(self.virtue_id, e))


if __name__ == "__main__":
    i = Introspect()
    i.set_virtue_id("Virtue_firefox123_1544115609")
    i.set_comms(["process_list", "kernel_modules"])
    i.set_interval(2)
    i.start()
    i.event.set()
    time.sleep(10)
    i.event.clear()
    time.sleep(10)
    i.event.set()
