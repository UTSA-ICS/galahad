# Transducer Control Mechanism

This code and readme is still in progress.

## Contents:

* filter/ - Syslog-ng module that decides whether to let messages pass or not based on status of transducer in ruleset (currently just a C program that should eventually be the listening thread)
* receiver.py - Listens for changes to 'commands' table in RethinkDB and forwards them on to the filter, waits for ACK from filter.  Also requests heartbeats from filter and updates DB.

## Setup:

* Install RethinkDB
* `python setup_rethinkdb.py`
* `cd filter; gcc filter.c cjson/cJSON.c map/src/map.c`

## To run:
* Start the filter "thread": `./a.out`
* Start the receiver: `python receiver.py <virtue_id>`.  For this example, assume virtue_id is "1".
* Run the excalibur CLI:
```
cd ../excalibur
python -m excalibur.cli
>>> transducer enable 1 msword_openfile {}
>>> transducer disable 1 msword_openfile
```
* You should see messages appearing on both the filter process's stdout and the receiver's stdout.
