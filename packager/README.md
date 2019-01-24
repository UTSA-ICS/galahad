# Galahad Packager

The packager is a tool to allow administrators on different Galahad systems to exchange roles encapsulated in a zip file. This will include the full JSON data about the role, each application, and each of the virtue's transducer's settings at the time of exporting. It will also include copies of each application's Docker container. Other metadata includes notes specified when exporting, an ID of the Galahad system it was exported from, a timestamp, and security-relevant user data.

When an admin wants to export a role, he must pass in the ID of a virtue created with that role. The reason for using a virtue to export a role is that transducer settings are not stored as part of a role.

## Dependencies

Python 3.6 or better. There are ZipFile functions that were introduced in 3.6 and are required by the packager.

Required packages:
    requests
    urllib3

Required commands:
    aws
    curl
    jq
    go

To import applications with the role, Docker must be installed. It is recommended that your Docker installation is clear of images before importing because `docker load` is called, and then cleaned up with `docker rm`. This requirement does not apply to exporting and interrogating.

## Directions

For a description of every available argument, run `$ ./packager.py -h`.

To export a virtue's role, run:
```
$ python3.6 packager.py -e <excalibur address> --export <virtue ID>
```
This will log into Excalibur, ask for human-readable notes pertaining to the role, and export the specified virtue's role to a file named "package.zip" (configurable with `-o`).

To examine a package's contents, run:
```
$ python3.6 packager.py --interrogate <package path>
```

To import a package, run:
```
$ python3.6 packager.py -e <excalibur address> --import <package path>
```
This will log you into Excalibur, examine existing roles and applications for ID conflicts, and prompt the admin for how to handle them, if any.