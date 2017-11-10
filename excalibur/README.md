# Excalibur server

Excalibur is a REST server that runs on port 8080 to manage Virtues
on AWS.  Excalibur can be started by running excalibur.py with no
arguments.

Commands can be issued to Excalibur through a web browser or with
the curl command using HTTP GET with the following format:

  EXCALIBUR_HOST:8080/COMMAND_GROUP?command=COMMAND?ARG=VALUE

For example, with Excalibur running on localhost, to create a new
Virtue instance using curl, run:

  curl 'localhost:8080/virtue?command=create&roleId=test-role'

Excalibur will return a Virtue structure (as described in the API
document) in JSON format.

# Prerequisites

Use `apt install` to install these packages prior to using Excalibur:

* python-webpy
* python-boto