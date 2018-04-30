# Transducer Control Mechanism

## Contents:

* merlin.py - On each Virtue, listens for changes to 'commands' table in RethinkDB and forwards them on to the filter, waits for ACK from filter.  Also requests heartbeats from filter and updates DB.
* listener.py - On Excalibur, listens for heartbeats coming from Merlin.  Alerts Elasticsearch directly if too many heartbeats are missed.
* transducer-module - A module for syslog-ng that filters messages according to the current ruleset that is set by the user through Excalibur and Merlin.

## Setup:

* To build merlin:
    * Put `rethinkdb_cert.pem`, `excalibur_pub.pem`, and `excalibur_key.pem` into `merlin/var/private/ssl/`
    * Run `./build_deb.sh merlin` from this (`galahad/transducers`) directory
    * This creates a deb file, which is given to the Assembler

* To build the heartbeat listener:
    * Look in `listener/opt/heartbeatlistener/.excalibur` and either copy all those keys into the specified paths, or change the paths to point to the keys' locations
    * Run `./build_deb.sh merlin` to build the listener deb file, which is installed on Excalibur

* To build the syslog-ng filter:
    * See `transducer-module/README.md`

* To set up RethinkDB:
    * As a docker container: `cd docker; docker-compose up -d`
    * On bare metal (run `install_rethinkdb.sh`):
        * In `/etc/hosts`, add `127.0.0.1 rethinkdb.galahad.lab`
        * Install rethinkdb:
            ```
            source /etc/lsb-release && echo "deb http://download.rethinkdb.com/apt $DISTRIB_CODENAME main" | sudo tee /etc/apt/sources.list.d/rethinkdb.list
            wget -qO- https://download.rethinkdb.com/apt/pubkey.gpg | sudo apt-key add -
            sudo apt-get update
            sudo apt-get install rethinkdb
            ```
        * Generate a certificate for the `rehtinkdb.galahad.lab` domain: `openssl req -new -x509 -key rethinkdb.pem -out rethinkdb_cert.pem -days 3650`
        * Put the key (`rethinkdb.pem`) and cert (`rethinkdb_cert.pem`) in `/var/private/ssl` and set permissions:
            ```
            sudo chown rethinkdb:rethinkdb /var/private/ssl/*.pem
            sudo chmod 600 /var/private/ssl/*.pem
            ```
        * Copy `rethinkdb.conf` to `/etc/rethinkdb/instances.d/`
        * Enable rethinkdb in systemctl and start it:
            ```
            sudo systemctl enable rethinkdb@rethinkdb
            sudo systemctl start rethinkdb@rethinkdb
            ```

* To set up Excalibur:
    * Add an entry to `/etc/hosts` that maps the ip address of the RethinkDB host to `rethinkdb.galahad.lab`
    * Set up RethinkDB by running: `python setup_rethinkdb.py -h [rethinkdb hostname] -c [path to rethinkdb ca cert]` (you will need all the python modules specified in `../excalibur/requirements.txt`)
    * Configure RethinkDB's admin password by running: `python set_admin_pw_rethinkdb.py -h [host] -c [cert]`.  NOTE: If you want to run this script again, you must add the current admin password to the `connect()` call.

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

* You should see heartbeat and control messages in /opt/merlin/merlin.log on the Virtue

