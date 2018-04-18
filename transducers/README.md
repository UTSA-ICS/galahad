# Transducer Control Mechanism

## Contents:

* merlin.py - On each Virtue, listens for changes to 'commands' table in RethinkDB and forwards them on to the filter, waits for ACK from filter.  Also requests heartbeats from filter and updates DB.
* listener.py - On Excalibur, listens for heartbeats coming from Merlin.  Alerts Elasticsearch directly if too many heartbeats are missed.
* transducer-module - A module for syslog-ng that filters messages according to the current ruleset that is set by the user through Excalibur and Merlin.

## Setup:

* To build merlin:
    * Put `rethinkdb_cert.pem`, `excalibur_pub.pem`, and `excalibur_key.pem` into `merlin/var/private/ssl/`
    * Run `dpkg-deb --build merlin` from this (`galahad/transducers`) directory
    * This creates a deb file, which is given to the Assembler

* To build the heartbeat listener:
    * Look in `listener/opt/heartbeatlistener/.excalibur` and either copy all those keys into the specified paths, or change the paths to point to the keys' locations
    * Run `dpkg-deb --build listener` to build the listener deb file, which is installed on Excalibur

* To build the syslog-ng filter:
    * See `transducer-module/README.md`

* To set up Excalibur:
    * Start RethinkDB with a config file similar to `docker/rethinkdb.conf`.  Make sure you have a cert that matches the domain name.
    * Edit `setup_rethinkdb.py` and `set_admin_pw_rethinkdb.py` to specify RethinkDB's host and cert location.
    * Set up RethinkDB by running: `python setup_rethinkdb.py` (you will need all the python modules specified in `../excalibur/requirements.txt`)
    * Configure RethinkDB's admin password by running: `python set_admin_pw_rethinkdb.py`.  NOTE: If you want to run this script again, you must add the current admin password to the `connect()` call.

## To run:
* The Virtue must be running syslog-ng (with transducer module) and Merlin (look in `merlin/etc/init.d/merlin` for runtime arguments)
* Make sure .excalibur exists in the directory from which you will be running the CLI.  Also make sure that it points to the correct hosts, keys, and certs.
* On excalibur, run the CLI. (For VIRTUE_ID, use whatever you specified when starting Merlin.  The init.d script uses "virtue_$(cat /etc/machine-id)")
```
cd ../excalibur
python -m excalibur.cli
>>> transducer enable <VIRTUE_ID> socket_connect {}
>>> transducer disable <VIRTUE_ID> socket_connect
```

* You should see heartbeat and control messages in /root/merlin.log on the Virtue

