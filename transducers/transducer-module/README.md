# Syslog-ng module building guide

## Prereqs

### Install dependencies

* Ensure all dependencies listed in Step 2 here https://syslog-ng.com/documents/html/syslog-ng-ose-latest-guides/en/syslog-ng-ose-guide-admin/html/compiling-syslog-ng.html are installed.  You can probably ignore installing gradle (it may be required by their build scripts), but the rest of the Java steps should be followed for our use case.

	- For glib on ubuntu, see https://www.linuxhelp.com/how-to-install-glib-2-0-on-ubuntu-17-04/
	- There is an unlisted OpenSSL dependency, on ubuntu install libssl-dev
	- There is an unlisted Libtool dependency, on ubuntu install libtool


### Install syslog-ng 

* On ubuntu, follow https://syslog-ng.com/blog/installing-the-latest-syslog-ng-on-ubuntu-and-other-deb-distributions/ substituting 17.04 for your distro version (tested on 16.04).  syslog-ng-core and syslog-ng-dev (and other syslog-ng modules) can now be installed from apt.  
	
	- This was tested with both syslog-ng-core and syslog-ng-dev installed

### Alert pkgconfig that syslog-ng exists

* The syslog-ng-incubator make tools require knowing where syslog-ng lives, they do this with pkgconfig.  Tell pkgconfig about syslogng by setting the following env variable:

	export PKG_CONFIG_PATH=/usr/lib/pkgconfig/

Note this is for ubuntu, the location of the .pc files associated with syslog-ng may be elsewhere on different distros.

## Install process

On a new setup, run 

	autoreconf -i
	./configure
	make
	make install

Note that the first command only needs to be run once when first setting up your build directory.  The second line should be run whenever your make file needs to change.  

Make install installs the module for you to your local syslog-ng envrionment.

## Using module

### Post install pre-req's 

The syslog-ng module currently sets the group of the unix domain socket to the "virtue" group.  Due to permission restrictions on the C chown call, the root user must be added to the "virtue" group prior to starting syslog-ng.  

Also, the directory a unix domain socket in effects the access permissions of unix domain sockets, so the directory the socket is placed in should also belong to the "virtue" group.  

### Socket Path

To select your socket path, using the following config for the transducer module with syslog-ng:

	parser transducer_controller {
	        transducer_controller(
	                socket("/var/run/receiver_to_filter")
	        );
	};
