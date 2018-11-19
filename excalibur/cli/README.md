# Galahad Command Line Interface

The command line interface for the Galahad system allows an administrator or a user to
control the Galahad system. This is optimized for the evaluation exercise, and the API
is designed to match the test and evaluation team's interface specification document.

To run the interactive CLI:

```
$ python3 interactive.py
```

This will drop you into a main loop. Type `help` to see available commands. Note that you will likely need to issue a `login` command before you can do anything useful.

From a design perspective, the CLI is controlled by a set of JSON files that define the commands available. If you want to add, modify, or remove any API methods, modify the appropriate JSON file.

To run the command-line only versions of the tools:

```
$ virtue [subcommands]
 -- or --
$ virtue-adm [subcommands]
 -- or --
$ virtue-security [subcommands]
```

Note that to use these tools, you'll need to set your user token through the login.sh script:

```

```

Notes:

- The Email and Password are the OAuth credentials for a user with admin privileges
- The default OATH APP name is currently the right one to use
- The supported commands within the admin CLI can be listed with the `help` command
