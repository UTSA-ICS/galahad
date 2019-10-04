#!/usr/bin/env python
import psutil
import json
import subprocess
import datetime
import threading
import logging
from handlers import CMRESHandler
import time
import fcntl

"""
This agent collects performance metrics and some categorical data about the system.
It uses psutil lib + nethogs tool for collecting the data
Output is in a multi-object (one per line) JSON file
"""

# Constants
CPU_RATE = "cpu_times"
CTX_RATE = "num_ctx_switches"
GID_RATE = "gids"
IOCOUNT_RATE = "io_counters"
IONICE_RATE = "ionice"
MEM_RATE = "memory_full_info"
NET_RATE = "network_info"
collection_rates = {}

elasticLog = logging.getLogger('elasticLog')
elasticHandler = CMRESHandler(hosts=[{'host': 'aggregator.galahad.com', 'port': 9200}],
    auth_type=CMRESHandler.AuthType.HTTPS,
    es_index_name="ossensor",
    use_ssl=True,
    verify_ssl=False,
    buffer_size=2,
    flush_frequency_in_sec=1000,
    ca_certs='/var/private/ssl/rethinkdb_cert.pem',
    client_cert='/var/private/ssl/kirk.crtfull.pem',
    client_key='/var/private/ssl/kirk.key.pem',
    auth_details=('admin', 'admin'),
    index_name_frequency=CMRESHandler.IndexNameFrequency.DAILY,
    raise_on_indexing_exceptions=True)

elasticLog.addHandler(elasticHandler)
elasticLog.setLevel(logging.INFO)

log = logging.getLogger('ossensor')
logfile = logging.FileHandler('/opt/ossensor/ossensor.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
logfile.setFormatter(formatter)
log.addHandler(logfile)
log.setLevel(logging.INFO)
log.info('Started OS Sensor')


# This thread collects data related to CPU
def get_cpu_times(args=None):

    global collection_rates
    while True:

        # Do nothing if collection rate is 0
        if collection_rates[CPU_RATE] == 0:
            time.sleep(10)
            continue

        procs = {}
        # Get list of all running processes
        for p in psutil.process_iter():
            proc = {}
            with p.oneshot():
                proc["timestamp"] = str(datetime.datetime.now())
                cpu_times = p.cpu_times()
                proc["cpu_times"] = {}
                proc["cpu_times"]["user"] = cpu_times.user
                proc["cpu_times"]["system"] = cpu_times.system
                proc["cpu_times"]["children_user"] = cpu_times.children_user
                proc["cpu_times"]["children_system"] = cpu_times.children_system
                proc["cpu_percent"] = p.cpu_percent()
                proc["create_time"] = p.create_time()
                proc["ppid"] = p.ppid()
                proc["status"] = p.status()
                proc["cpu_num"] = p.cpu_num()
                proc["num_threads"] = p.num_threads()

                proc["pid"] = p.pid
                proc["name"] = p.name()
                proc["cwd"] = p.cwd()
                proc["nice"] = p.nice()
                proc["num_fds"] = p.num_fds()

                cmdline = p.cmdline()
                if cmdline:
                    proc["cmdline"] = cmdline[0]
                else:
                    proc["cmdline"] = []

                procs[proc["pid"]] = proc

        elasticLog.info(str(procs))

        time.sleep(collection_rates[CPU_RATE])


def get_ctx_switch_data(args=None):

    global collection_rates
    while True:

        # Do nothing if collection rate is 0
        if collection_rates[CTX_RATE] == 0:
            time.sleep(10)
            continue

        procs = {}

        for p in psutil.process_iter():
            proc = {}
            with p.oneshot():
                num_ctx_switches = p.num_ctx_switches()
                proc["num_ctx_switches"] = {}
                proc["num_ctx_switches"]["voluntary"] = num_ctx_switches.voluntary
                proc["num_ctx_switches"]["involuntary"] = num_ctx_switches.involuntary

                proc["timestamp"] = str(datetime.datetime.now())
                proc["pid"] = p.pid
                proc["name"] = p.name()
                proc["cwd"] = p.cwd()
                proc["nice"] = p.nice()
                proc["num_fds"] = p.num_fds()

                cmdline = p.cmdline()
                if cmdline:
                    proc["cmdline"] = cmdline[0]
                else:
                    proc["cmdline"] = []

                procs[proc["pid"]] = proc

        elasticLog.info(str(procs))

        time.sleep(collection_rates[CTX_RATE])


def get_gids_data(args=None):

    global collection_rates
    while True:

        # Do nothing if collection rate is 0
        if collection_rates[GID_RATE] == 0:
            time.sleep(10)
            continue

        procs = {}

        for p in psutil.process_iter():
            proc = {}
            with p.oneshot():
                gids = p.gids()
                proc["gids"] = {}
                proc["gids"]["real"] = gids.real
                proc["gids"]["effective"] = gids.effective
                proc["gids"]["saved"] = gids.saved

                proc["timestamp"] = str(datetime.datetime.now())
                proc["pid"] = p.pid
                proc["name"] = p.name()
                proc["cwd"] = p.cwd()
                proc["nice"] = p.nice()
                proc["num_fds"] = p.num_fds()

                cmdline = p.cmdline()
                if cmdline:
                    proc["cmdline"] = cmdline[0]
                else:
                    proc["cmdline"] = []

                procs[proc["pid"]] = proc

        elasticLog.info(str(procs))

        time.sleep(collection_rates[GID_RATE])


def get_iocount_data(args=None):

    global collection_rates
    while True:

        # Do nothing if collection rate is 0
        if collection_rates[IOCOUNT_RATE] == 0:
            time.sleep(10)
            continue

        procs = {}

        for p in psutil.process_iter():
            proc = {}
            with p.oneshot():
                io_counters = p.io_counters()
                proc["io_counters"] = {}
                proc["io_counters"]["read_count"] = io_counters.read_count
                proc["io_counters"]["write_count"] = io_counters.write_count
                proc["io_counters"]["read_bytes"] = io_counters.read_bytes
                proc["io_counters"]["write_bytes"] = io_counters.write_bytes
                proc["io_counters"]["read_chars"] = io_counters.read_chars
                proc["io_counters"]["write_chars"] = io_counters.write_chars

                proc["timestamp"] = str(datetime.datetime.now())
                proc["pid"] = p.pid
                proc["name"] = p.name()
                proc["cwd"] = p.cwd()
                proc["nice"] = p.nice()
                proc["num_fds"] = p.num_fds()

                cmdline = p.cmdline()
                if cmdline:
                    proc["cmdline"] = cmdline[0]
                else:
                    proc["cmdline"] = []

                procs[proc["pid"]] = proc

        elasticLog.info(str(procs))

        time.sleep(collection_rates[IOCOUNT_RATE])


def get_ionice_data(args=None):

    global collection_rates
    while True:

        # Do nothing if collection rate is 0
        if collection_rates[IONICE_RATE] == 0:
            time.sleep(10)
            continue

        procs = {}

        for p in psutil.process_iter():
            proc = {}
            with p.oneshot():
                ionice = p.ionice()
                proc["ionice"] = {}
                proc["ionice"]["ioclass"] = ionice.ioclass
                proc["ionice"]["value"] = ionice.value

                proc["timestamp"] = str(datetime.datetime.now())
                proc["pid"] = p.pid
                proc["name"] = p.name()
                proc["cwd"] = p.cwd()
                proc["nice"] = p.nice()
                proc["num_fds"] = p.num_fds()

                cmdline = p.cmdline()
                if cmdline:
                    proc["cmdline"] = cmdline[0]
                else:
                    proc["cmdline"] = []

                procs[proc["pid"]] = proc

        elasticLog.info(str(procs))

        time.sleep(collection_rates[IONICE_RATE])


def get_memory_full_data(args=None):

    global collection_rates
    while True:

        # Do nothing if collection rate is 0
        if collection_rates[MEM_RATE] == 0:
            time.sleep(10)
            continue

        procs = {}

        for p in psutil.process_iter():
            proc = {}
            with p.oneshot():
                # Values are in bytes
                memory_full_info = p.memory_full_info()
                proc["memory_full_info"] = {}
                proc["memory_full_info"]["rss"] = memory_full_info.rss
                proc["memory_full_info"]["vms"] = memory_full_info.vms
                proc["memory_full_info"]["shared"] = memory_full_info.shared
                proc["memory_full_info"]["text"] = memory_full_info.text
                proc["memory_full_info"]["data"] = memory_full_info.data
                proc["memory_full_info"]["lib"] = memory_full_info.lib
                proc["memory_full_info"]["dirty"] = memory_full_info.dirty
                proc["memory_full_info"]["uss"] = memory_full_info.uss
                proc["memory_full_info"]["pss"] = memory_full_info.pss
                proc["memory_full_info"]["swap"] = memory_full_info.swap

                proc["timestamp"] = str(datetime.datetime.now())
                proc["pid"] = p.pid
                proc["name"] = p.name()
                proc["cwd"] = p.cwd()
                proc["nice"] = p.nice()
                proc["num_fds"] = p.num_fds()

                cmdline = p.cmdline()
                if cmdline:
                    proc["cmdline"] = cmdline[0]
                else:
                    proc["cmdline"] = []

                procs[proc["pid"]] = proc

        elasticLog.info(str(procs))

        time.sleep(collection_rates[MEM_RATE])


# This thread collects data related to network data
def get_nethogs_data(args=None):

    global collection_rates
    while True:

        # Do nothing if collection rate is 0
        if collection_rates[NET_RATE] == 0:
            time.sleep(10)
            continue

        procs = {}

        for p in psutil.process_iter():
            proc = {}
            with p.oneshot():
                proc["timestamp"] = str(datetime.datetime.now())
                proc["pid"] = p.pid
                proc["name"] = p.name()
                proc["cwd"] = p.cwd()
                proc["nice"] = p.nice()
                proc["num_fds"] = p.num_fds()

                cmdline = p.cmdline()
                if cmdline:
                    proc["cmdline"] = cmdline[0]
                else:
                    proc["cmdline"] = []

                proc["network_info"] = {"kb_sent": 0.0, "kb_received": 0.0}
                # proc["environ"] = p.environ()
                procs[proc["pid"]] = proc

        # Get the network info about each process if available (or active)
        proc = subprocess.Popen(["nethogs", "-t", "-d", "1", "-c", str(collection_rates[NET_RATE])], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        lines = out.split("\n")
        ref_found = False
        p = {}

        # Parsing nethogs output
        # Assuming that all output lines in nethogs contains 3 tokens (pname+id, sent, recv) once the "Refreshing" word is found
        # EX: /opt/google/chrome/chrome/17558/1000 0.0128906 0.0128906
        # EX: php-fpm: pool www/2187/33 35.2465 44.2551
        for line in lines:
            if ref_found:
                words = line.split()
                if words and words[0] != "unknown" and len(words) >= 3:
                    # /opt/google/chrome/chrome/8532/1000 => pid = 8532

                    # Should check this condition
                    if len(words[-3].split("/")) < 2:
                        continue
                    pid = words[-3].split("/")[-2]
                    pid = int(pid.strip())
                    # Unknown traffic (e.g. NFS mounted files)
                    if pid == 0:
                        continue
                    if pid not in p:
                        p[pid] = {"kb_sent": 0.0, "kb_received": 0.0, "cnt": 0}
                    p[pid]["kb_sent"] += float(words[-2])
                    p[pid]["kb_received"] += float(words[-1])
                    p[pid]["cnt"] += 1
                    # print procs[pid]
            if "Refreshing" in line:
                ref_found = True
        for pid in p:
            if pid in procs:
                procs[pid]["network_info"]["kb_sent"] = p[pid]["kb_sent"] / p[pid]["cnt"]
                procs[pid]["network_info"]["kb_received"] = p[pid]["kb_received"] / p[pid]["cnt"]

        elasticLog.info(str(procs))


# Get data about all processes
def get_procs_data(coll_rate):
    procs = {}
    # Get list of all running processes
    for p in psutil.process_iter():
        proc = {}
        with p.oneshot():
            proc["timestamp"] = str(datetime.datetime.now())

            cpu_times = p.cpu_times()
            proc["cpu_times"] = {}
            proc["cpu_times"]["user"] = cpu_times.user
            proc["cpu_times"]["system"] = cpu_times.system
            proc["cpu_times"]["children_user"] = cpu_times.children_user
            proc["cpu_times"]["children_system"] = cpu_times.children_system

            num_ctx_switches = p.num_ctx_switches()
            proc["num_ctx_switches"] = {}
            proc["num_ctx_switches"]["voluntary"] = num_ctx_switches.voluntary
            proc["num_ctx_switches"]["involuntary"] = num_ctx_switches.involuntary

            gids = p.gids()
            proc["gids"] = {}
            proc["gids"]["real"] = gids.real
            proc["gids"]["effective"] = gids.effective
            proc["gids"]["saved"] = gids.saved

            io_counters = p.io_counters()
            proc["io_counters"] = {}
            proc["io_counters"]["read_count"] = io_counters.read_count
            proc["io_counters"]["write_count"] = io_counters.write_count
            proc["io_counters"]["read_bytes"] = io_counters.read_bytes
            proc["io_counters"]["write_bytes"] = io_counters.write_bytes
            proc["io_counters"]["read_chars"] = io_counters.read_chars
            proc["io_counters"]["write_chars"] = io_counters.write_chars

            # Values are in bytes
            memory_full_info = p.memory_full_info()
            proc["memory_full_info"] = {}
            proc["memory_full_info"]["rss"] = memory_full_info.rss
            proc["memory_full_info"]["vms"] = memory_full_info.vms
            proc["memory_full_info"]["shared"] = memory_full_info.shared
            proc["memory_full_info"]["text"] = memory_full_info.text
            proc["memory_full_info"]["data"] = memory_full_info.data
            proc["memory_full_info"]["lib"] = memory_full_info.lib
            proc["memory_full_info"]["dirty"] = memory_full_info.dirty
            proc["memory_full_info"]["uss"] = memory_full_info.uss
            proc["memory_full_info"]["pss"] = memory_full_info.pss
            proc["memory_full_info"]["swap"] = memory_full_info.swap

            ionice = p.ionice()
            proc["ionice"] = {}
            proc["ionice"]["ioclass"] = ionice.ioclass
            proc["ionice"]["value"] = ionice.value

            proc["cpu_percent"] = p.cpu_percent()
            proc["create_time"] = p.create_time()
            proc["ppid"] = p.ppid()
            proc["status"] = p.status()
            proc["cpu_num"] = p.cpu_num()
            proc["num_threads"] = p.num_threads()

            proc["pid"] = p.pid
            proc["name"] = p.name()
            proc["cwd"] = p.cwd()
            proc["nice"] = p.nice()
            proc["num_fds"] = p.num_fds()

            cmdline = p.cmdline()
            if cmdline:
                proc["cmdline"] = cmdline[0]
            else:
                proc["cmdline"] = []

            proc["network_info"] = {"kb_sent": 0.0, "kb_received": 0.0}
            # proc["environ"] = p.environ()
            procs[proc["pid"]] = proc

    # Get the network info about each process if available (or active)
    proc = subprocess.Popen(["nethogs", "-t", "-d", "1", "-c", str(coll_rate)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    lines = out.split("\n")
    ref_found = False
    p = {}

    # Parsing nethogs output
    # Assuming that all output lines in nethogs contains 3 tokens (pname+id, sent, recv) once the "Refreshing" word is found
    # EX: /opt/google/chrome/chrome/17558/1000 0.0128906 0.0128906
    # EX: php-fpm: pool www/2187/33 35.2465 44.2551
    for line in lines:
        if ref_found:
            words = line.split()
            if words and words[0] != "unknown" and len(words) >= 3:
                # /opt/google/chrome/chrome/8532/1000 => pid = 8532

                # Should check this condition
                if len(words[-3].split("/")) < 2:
                    continue
                pid = words[-3].split("/")[-2]
                pid = int(pid.strip())
                # Unknown traffic (e.g. NFS mounted files)
                if pid == 0:
                    continue
                if pid not in p:
                    p[pid] = {"kb_sent": 0.0, "kb_received": 0.0, "cnt": 0}
                p[pid]["kb_sent"] += float(words[-2])
                p[pid]["kb_received"] += float(words[-1])
                p[pid]["cnt"] += 1
                # print procs[pid]
        if "Refreshing" in line:
            ref_found = True
    for pid in p:
        if pid in procs:
            procs[pid]["network_info"]["kb_sent"] = p[pid]["kb_sent"] / p[pid]["cnt"]
            procs[pid]["network_info"]["kb_received"] = p[pid]["kb_received"] / p[pid]["cnt"]
    return procs


def main():

    # Start threads to begin collecting data
    t_cpu = threading.Thread(target=get_cpu_times).start()
    t_ctx = threading.Thread(target=get_ctx_switch_data).start()
    t_gid = threading.Thread(target=get_gids_data).start()
    t_iocount = threading.Thread(target=get_iocount_data).start()
    t_ionice = threading.Thread(target=get_ionice_data).start()
    t_memory = threading.Thread(target=get_memory_full_data).start()
    t_net = threading.Thread(target=get_nethogs_data).start()

    # Wait for changes to ossensor-config file to update thread collection rates
    while True:
        with open('/opt/ossensor/ossensor-config.json', 'r') as f:
            # Acquire file lock
            while True:
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except IOError as e:
                    # raise on unrelated IOErrors
                    if e.errno != errno.EAGAIN:
                        raise
                    else:
                        time.sleep(0.1)

            config = json.load(f)
            fcntl.flock(f, fcntl.LOCK_UN)

        if "rates" not in config:
            collection_rates[CPU_RATE] = 0.0
            collection_rates[CTX_RATE] = 0.0
            collection_rates[GID_RATE] = 0.0
            collection_rates[IOCOUNT_RATE] = 0.0
            collection_rates[IONICE_RATE] = 0.0
            collection_rates[MEM_RATE] = 0.0
            collection_rates[NET_RATE] = 0.0
            time.sleep(5)
            continue

        collection_rates[CPU_RATE] = config['rates'].get(CPU_RATE, 0.0)
        collection_rates[CTX_RATE] = config['rates'].get(CTX_RATE, 0.0)
        collection_rates[GID_RATE] = config['rates'].get(GID_RATE, 0.0)
        collection_rates[IOCOUNT_RATE] = config['rates'].get(IOCOUNT_RATE, 0.0)
        collection_rates[IONICE_RATE] = config['rates'].get(IONICE_RATE, 0.0)
        collection_rates[MEM_RATE] = config['rates'].get(MEM_RATE, 0.0)
        collection_rates[NET_RATE] = config['rates'].get(NET_RATE, 0.0)

        time.sleep(5)

    # f.write(json_str + "\n")
    # elasticLog.info("OS Sensor: " + json_str)


if __name__ == "__main__":

    # Setup initial collection rates
    collection_rates[CPU_RATE] = 0.0
    collection_rates[CTX_RATE] = 0.0
    collection_rates[GID_RATE] = 0.0
    collection_rates[IOCOUNT_RATE] = 0.0
    collection_rates[IONICE_RATE] = 0.0
    collection_rates[MEM_RATE] = 0.0
    collection_rates[NET_RATE] = 0.0
    main()
