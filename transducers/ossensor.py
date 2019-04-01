#!/usr/bin/env python
import psutil
import json
import subprocess
from subprocess import call
import datetime
import threading
import socket
import logging
from handlers import CMRESHandler


"""
This agent collects performance metrics and some categorical data about the system.
It uses psutil lib + nethogs tool for collecting the data
Output is in a multi-object (one per line) JSON file
"""


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

#Get data about all processes
def get_procs_data(coll_rate):
    procs = {}
    #Get list of all running processes
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

            #Values are in bytes
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
            #proc["environ"] = p.environ()
            procs[proc["pid"]] = proc

    #Get the network info about each process if available (or active)
    proc = subprocess.Popen(["nethogs", "-t", "-d", "1", "-c", str(coll_rate)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    lines = out.split("\n")
    ref_found = False
    p = {}
    
    #Parsing nethogs output
    #Assuming that all output lines in nethogs contains 3 tokens (pname+id, sent, recv) once the "Refreshing" word is found
    #EX: /opt/google/chrome/chrome/17558/1000 0.0128906 0.0128906
    #EX: php-fpm: pool www/2187/33 35.2465 44.2551
    for line in lines:
        if ref_found:
            words = line.split()
            if words and words[0] != "unknown" and len(words) >= 3:
                #/opt/google/chrome/chrome/8532/1000 => pid = 8532
                pid = words[-3].split("/")[-2]
                pid = int(pid.strip())
                #Unknown traffic (e.g. NFS mounted files)
                if pid == 0:
                    continue
                if pid not in p:
                    p[pid] = {"kb_sent": 0.0, "kb_received": 0.0, "cnt": 0}
                p[pid]["kb_sent"] += float(words[-2])
                p[pid]["kb_received"] += float(words[-1])
                p[pid]["cnt"] += 1
                #print procs[pid]
        if "Refreshing" in line:
            ref_found = True
    for pid in p:
        if pid in procs:
            procs[pid]["network_info"]["kb_sent"] = p[pid]["kb_sent"] / p[pid]["cnt"]
            procs[pid]["network_info"]["kb_received"] = p[pid]["kb_received"] / p[pid]["cnt"]
    return procs

def main(f, coll_rate):
    #Collect data every 10 seconds
    threading.Timer(coll_rate, main, [f, coll_rate]).start()
    
    procs = get_procs_data(coll_rate)
    json_str = json.dumps(procs)

    f.write(json_str + "\n")
    elasticLog.info("OS Sensor: " + json_str)
if __name__ == "__main__":
    

    #Collection frequency in secs
    coll_rate = 10.0
    with open('/etc/machine-id') as f:
        #[:-1] for omitting the extra '\n'
        VM_id = f.readline()[:-1]

    fpath = "/home/virtue/stats-%s-%s.txt" % (socket.gethostname(), VM_id)
    f = open(fpath, 'w')
    main(f, coll_rate)
