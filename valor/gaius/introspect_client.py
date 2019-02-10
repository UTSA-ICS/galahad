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
    def __init__(self, virtue_id, comms, interval):
        self.virtue_id = virtue_id
        self.interval = interval
        self.comms = comms
        self.libvmi_entry = self.add_virtue_to_libvmi()

        # Block the thread using the Event Object
        threading.Thread.__init__(self)
        self.event = threading.Event()
        self.event.set()

    def run(self):
        self.event.wait()
        # Process while loop only till the event is set.
        # When the event is cleared then exit while loop and the thread
        while self.event.is_set():
            for comm in self.comms:
                getattr(self, comm)()
            time.sleep(self.interval)

    def stop_introspect(self):
        self.event.clear()
        # Cleanup the libvmi file before exiting.
        self.remove_virtue_from_libvmi()

    def add_virtue_to_libvmi(self):
        with open("/etc/libvmi.conf") as f:
            contents = f.read()

        first_entry = contents.split('}')[0]
        id = first_entry.split(' ')[0]
        body = first_entry.replace(id + ' ', '') + '}\n'

        virtue_entry = self.virtue_id + ' ' + body

        with open("/etc/libvmi.conf", "w") as f:
            f.write(contents + virtue_entry)

        return virtue_entry

    def remove_virtue_from_libvmi(self):
        with open("/etc/libvmi.conf") as f:
            contents = f.read()

        # Remove entry from libvmi file
        with open("/etc/libvmi.conf", "w") as f:
            f.write(contents.replace(self.libvmi_entry, ''))

    def set_interval(self, interval):
        self.interval = interval

    def set_comms(self, comms):
        self.comms = comms

    def process_list(self):
        try:
            out = subprocess.check_output(
                "echo \"process-list {}\" | nc -U /tmp/control.socket".format(
                    self.virtue_id), stderr=subprocess.STDOUT, shell=True)
            intro_logger.debug("process-list {}: {}".format(self.virtue_id, out))
        except subprocess.CalledProcessError as e:
            intro_logger.debug("process-list {}: {}".format(self.virtue_id, e))

    def kernel_modules(self):
        try:
            out = subprocess.check_output(
                "echo \"kernel-modules {}\" | nc -U /tmp/control.socket".format(
                    self.virtue_id), stderr=subprocess.STDOUT, shell=True)
            intro_logger.debug("kernel-modules {}: {}".format(self.virtue_id, out))
        except subprocess.CalledProcessError as e:
            intro_logger.debug("kernel-modules {}: {}".format(self.virtue_id, e))

    def inspect_virtue_lsm(self):
        try:
            out = subprocess.check_output(
                "echo \"inspect-virtue-lsm {}\" | nc -U /tmp/control.socket".format(
                    self.virtue_id), stderr=subprocess.STDOUT, shell=True)
            intro_logger.debug("inspect-virtue-lsm {}: {}".format(self.virtue_id, out))
        except subprocess.CalledProcessError as e:
            intro_logger.debug("inspect-virtue-lsm {}: {}".format(self.virtue_id, e))


if __name__ == "__main__":
    i = Introspect("Virtue_firefox123_1544115609", ["process_list", "kernel_modules"], 2)
    i.start()
    i.event.set()
    time.sleep(10)
    i.event.clear()
