# EXCALIBUR

Excalibur is the API endpoint for the Galahad system. You can interact with it in a variety of ways, including:

- Command line read-eval-print loop (REPL)
- REST API
- Some other ways, probably

NOTE that the transducer functionality needs either to have the `.excalibur` config file (if using the command line interface (CLI)) or to manually call `set_api_config()` with the appropriate configuration object (if using the REST API).

## REPL Loop

The Excalibur REPL loop is designed to be run out of a Python virtual environment (venv). 


```
$ . /path/to/venv/bin/activate
$ cd /path/to/galahad/excalibur
$ pip install -r requirements.txt
$ cd ..
$ python -m website.cli
```

This will launch an Excalibur "command prompt" where you can interact with the API endpoints. 

Note that you first need to log in: 

```
==> login [username] [password]
```

And then you call the command you want (with underscores in place of spaces), with ALL of the arguments that it takes (including username, if that's part of the implementation's argument list).  For example:
* `transducer_list [username]`
* `user_list`
* `virtue_get [username] [virtue_id]`

