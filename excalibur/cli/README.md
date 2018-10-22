# Galahad Command Line Interface

The command line interface for the Galahad system allows an administrator or a user to
control the Galahad system. This is optimized for the evaluation exercise, and the API
is designed to match the test and evaluation team's interface specification document.

To run the existing CLI:

```
$ python3 admin.py
Excalibur address: 127.0.0.1
Email: jmitchell@virtue.com
Password: Test123!
OAuth APP name (Default name 'APP_1' Press Enter):
```

Notes:

- The Email and Password are the OAuth credentials for a user with admin privileges
- The default OATH APP name is currently the right one to use
- The supported commands within the admin CLI can be listed with the `help` command
