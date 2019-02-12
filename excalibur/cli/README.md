# Galahad Command Line Interface

The command line interface for the Galahad system allows an administrator or a user to control the Galahad system. This is optimized for the evaluation exercise, and the API is designed to match the test and evaluation team's interface specification document.

## Interactive CLI

To run the interactive CLI:

```
$ python3 interactive.py
```

This will drop you into a main loop. Type `help` to see available commands. Note that you will likely need to issue a `login` command before you can do anything useful.

From a design perspective, the CLI is controlled by a set of JSON files that define the commands available. If you want to add, modify, or remove any API methods, modify the appropriate JSON file.

## Non-Interactive CLI

The CLI also exists as a set of standalone scripts suitable for use in scripts. To run the non-interactive versions of the tools:

For the user API: 

```
$ virtue [subcommands]
```

For the Administrator API:

```
$ virtue-admin [subcommands]
 ```

For the Security API:

```
$ virtue-security [subcommands]
```

Note that to use these tools, you'll need to set your user token through the login script:

```
$ python sso_login.py -h
usage: sso_login.py [-h] -u USER [-p PASSWORD] [-o OUTFILE] [-A APPID] server

Log in to Excalibur and save the user token

positional arguments:
  server                Server address

optional arguments:
  -h, --help                        show this help message and exit
  -u USER, --user USER              Username to log in with
  -p PASSWORD, --password PASSWORD  Password to use. If not specified, will prompt.
  -o OUTFILE, --outfile OUTFILE     File to write access token to (default is usertoken.json)
  -A APPID, --appid APPID           Application ID to use (default is APP_1)

$ python sso_login.py -u jmitchell@virtue.gov -o token.json 54.172.77.13:5002
```

You'll also have to set some environment variables, either on the command line, or in your environment, in order for the CLI to know where things are:

```
$ VIRTUE_ADDRESS=54.172.77.13 VIRTUE_TOKEN=`cat token.json` ./virtue-admin [...]
```

Notes:

- The Email and Password are the OAuth credentials for a user with admin privileges
- The default OATH APP name is currently the right one to use (APP_1)
- The supported commands within the admin CLI can be listed with the `help` command
