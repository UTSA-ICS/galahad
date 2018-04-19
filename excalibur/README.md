# EXCALIBUR

Excalibur is the API endpoint for the Galahad system. You can interact with it in a variety of ways, including:

- Command line read-eval-print loop (REPL)
- REST API
- Some other ways, probably

## REPL Loop

The Excalibur REPL loop is designed to be run out of a Python virtual environment (venv). 


```
$ . /path/to/venv/bin/activate
$ cd /path/to/galahad/excalibur
$ pip install -r requirements.txt
$ cd ..
$ python -m excalibur.cli
```

This will launch an Excalibur "command prompt" where you can interact with the API endpoints. For example:

```
==> help

Documented commands (type help <topic>):
========================================
help  transducer  verbose

Undocumented commands:
======================
EOF  exit

==> transducer help

Documented commands (type help <topic>):
========================================
disable  enable  get  get_configuration  get_enabled  help  list  list_enabled
```

You can even tab-complete, and use the normal readline functionality like pressing the up arrow to go back in history, etc.