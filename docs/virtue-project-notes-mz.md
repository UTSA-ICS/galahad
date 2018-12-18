# Maria's Virtue Notes

Everything I could think of that I know about Virtue, in the hopes that it will be helpful to someone.

## Overview of current transducers setup:

- See `virtue-design-diagram-mz.pptx` for a visual aid.
- When a Virtue starts up, Excalibur sends `transducer enable` and `transducer disable` commands.
- These commands get written to RethinkDB, into the `commands` table.
- The Virtue has several services that start on boot.  One of these is Merlin.  Merlin sees that there is no current transducer ruleset for this Virtue and looks in the RethinkDB `commands` table.  This retrieves the settings that Excalibur sent and validates the signature.  Merlin implements these settings by sending them out to the appropriate places.
	- Sensor settings are sent to the syslog-ng transducers module.  This module receives all event messages from the Linux Security Module and the Wine Instrumentation but only forwards to ElasticSearch the ones for which it received "enable" settings.
	- kill_proc actuator settings are sent to the Linux Security Module and to the Process Killer service.  The Process Killer stops the already running processes, which the LSM prevents new instances of these processes from starting.
	- net_block actuator settings are sent to the net_block kernel module.
- Once the settings are implemented, Merlin sends back an ACK by writing the current state of the transducer(s) to the `acks` table in RethinkDB.  In effect, this table is a mirror of what the current transducer state on each Virtue.
	- The kill_proc and net_block actuators also send syslog/ElasticSearch messages when they have killed/blocked something.
- All transducers send their messages to syslog.  Syslog-ng listens for messages on syslog and forwards them to ElasticSearch.
- Merlin continues to listen for further instructions on what transducers to enable or disable.
- Merlin also sends heartbeat messages every 30 seconds.  These messages are written to the `acks` table in RethinkDB and contain the current ruleset.  On the Excalibur instance, a Heartbeat Listener is running and checking for these heartbeat messages.  If three minutes go by without any messages, it sends alerts ElasticSearch.
- The Valor runs a process called Gaius, which listens for messages from RethinkDB and implements Virtue migration and can request an update from the introspection monitor.  The results of these actions are also written to syslog-ng, which forwards them on to ElasticSearch.  [ Correct this if it's wrong, I don't know the details but am including for completeness. ]
- The user can read the event messages via the UI provided by Kibana or by directly querying ElasticSearch.  They can also access higher-level statistics through the Blue Force Tracker.

## Debugging:

- To start a stack, run the `test_setup` job on Jenkins: `http://35.170.157.4:8080`.
- One way to start up a Virtue is to run the security tests from Excalibur: `cd galahad/tests/integration; pytest test_security_api.py`.  
	- You should comment out the teardown method at the end so that your Virtue doesn't get deleted.  
	- You can also comment out most of the tests, but make sure to leave a call to `__setup_virtue()`.  
	- You can rerun the security tests on an existing virtue if you create files called `virtue_ip` and `virtue_id`.
- To figure out a running Virtue's IP address: use the Blue Force Tracker or query LDAP directly (`ldapsearch -H ldap://localhost -D cn=admin,dc=canvas,dc=virtue,dc=com -W -b dc=canvas,dc=virtue,dc=com`, `Test123!`)
- SSHing to a Virtue: ssh to Excalibur first, then `ssh -i ~/default-user-key.pem virtue@10.91.0.[REST OF VIRTUE IP]`
- If transducer tests are failing, here are some things to check:
	- Is Merlin running on the Virtue at all? (`ps aux`) If not, check if it failed during startup: `cat /opt/merin/merlin-initd.log`
	- Check Merlin logs: `cat /opt/merlin/merlin.log`.  Did it receive any messages?  It prints to the log any time it receives a message from RethinkDB.  It also prints every time it sends a heartbeat message, which is every 30 seconds, so you should see if it's still functioning or when it stopped.
	- You can also go onto RethinkDB and print out the database to see if it got any of the messages (look in the "commands" table, ignore anything about migration).  To do this, from Excalibur `ssh -i ~/default-user-key.pem ubuntu@170.30.1.45` and run `galahad/transducers/print_db.py` (not present on the RethinkDB machine by default).
	- If the kill_proc actuator is failing, check that `processkiller.py` is running (can be started with `sudo systemctl start processkiller`).  Then check this log: `cat /opt/processkiller/processkiller.log`.  There's also a `processkiller-initd.log` in case something goes wrong during startup.  As mentioned before, check that Merlin is actually receiving the transducer enable/disable message.
	- If the net_block actuator is failing, ask Zach.  I believe there's still a binary somewhere on the Virtue that allows you to send a manual command to the net_block module.
		- Building the netblock actuator deb file:
		```
		#!/bin/bash
		#There should be a directory called
		# /usr/src/actuator_network-0.1/
		# with all of the files for the network
		# actuator copied to it.
		sudo apt-get install dh-make
		sudo apt-get install dkms
		sudo dkms remove actuator_network/0.1 --all
		sudo dkms add -m actuator_network -v 0.1
		sudo dkms build -m actuator_network -v 0.1
		sudo dkms mkdeb -m actuator_network -v 0.1
		sudo cp /var/lib/dkms/actuator_network/0.1/deb/actuator-network-dkms_0.1_all.deb .
		sudo mv actuator-network-dkms_0.1_all.deb netblock_actuator.deb
		```
	- Try restarting Merlin.  Try restarting Excalibur.  Worst case, start a new stack / new Virtue.
	- Basically this boils down to trying each part of the pipeline to see where the message is getting lost: test/cli -> REST wrapper (virtue.py) -> API endpoint -> RethinkDB -> Merlin -> syslog-ng/LSM/Process Killer/Network Blocker/etc -> ElasticSearch
- XPRA - how to connect to XPRA directly, without Canvas:
	- On excalibur:
		```
		ssh -i ~/default-user-key.pem -L 8200:127.0.0.1:PORT -N virtue@VIRTUE_IP_ADDR
		ssh -i ~/default-user-key.pem -L 10000:127.0.0.1:2023 -p 8200 -N virtue@127.0.0.1
		```
	- On local machine:
		```
		ssh -i ~/.ssh/starlab-virtue-te.pem -L 10000:127.0.0.1:10000 -N ubuntu@EXCALIBUR_IP_ADDR
		```
	- In a browser on your local machine, go to `localhost:10000`.
	- Make sure to change PORT, VIRTUE_IP_ADDR, and EXCALIBUR_IP_ADDR, as well as the path to your key on your local machine.  PORT comes from https://github.com/starlab-io/docker-virtue/blob/master/virtue/VirtueDockerConf.yaml (first two digits will be 67).
- LDAP - querying LDAP directly:
	- SSH to Excalibur
	- `ldapsearch -H ldap://localhost -D cn=admin,dc=canvas,dc=virtue,dc=com -W -b dc=canvas,dc=virtue,dc=com`
	- `Test123!`
- Restarting Excalibur service:
	```
	screen -ls
	screen -X -S Virtue quit
	cd galahad/excalibur
	./start-screen.sh
	```
- How to start an application on a Virtue manually (or debug):
	- (We are essentially mirroring `galahad/assembler/stages/virtued.py`)
	- SSH to the Virtue
	```
	git clone git@github.com:starlab-io/docker-virtue.git
	cd docker-virtue/virtue
	sudo [DOCKER LOGIN]
	sudo ./run.py -pr start [ONE OR MORE CONTAINERS TO START]
	# -p means to pull down the container
	# -r means it should restart if it ever dies
	```
	- Docker login comes from running `docker-virtue/virtue/get_docker_login_command.sh`.  Type in your MFA when it asks and it will give you a lot of text.  You want to run the line that starts with "docker login -u AWS -p" and continues for 20 more lines.
	- Container names that this script recognizes come from `docker-virtue/virtue/VirtueDockerConf.yaml`.
	- You can also try pulling the container yourself if that's not working: `sudo docker pull 703915126451.dkr.ecr.us-east-2.amazonaws.com/starlab-virtue:IMAGE_NAME` (note that the image name comes from the same `VirtueDockerConf.yaml` file, usually it's `virtue-CONTAINERNAME`)
- More about docker images:
	- There are two Elastic Container Registries on our AWS account.  They are both under the us-east-2 (Ohio) region!
	- To rebuild all our docker containers, run the Jenkins job called `docker-build`: `http://35.170.157.4:8080/view/all/job/docker-virtue/`
	- This will push all the containers to the starlab-virtue-ci ECR, for your testing/debugging convenience.
	- Once you're sure that the containers in starlab-virtue-ci are correct, you can run `virtue-docker/virtue/publish.py`, which will pull all those containers from starlab-virtue-ci and push them to starlab-virtue: `python3 publish.py -l -e office-word -e office-outlook`.  This is the repo that the official Virtue assembly process uses.
	- Note that we're skipping Word and Outlook.  These require extra work.  See: https://github.com/starlab-io/docker-virtue/tree/master/virtue#updating-containers


## Additional info:

- Applications:
	- There's a virtue gmail account for testing email: bbnvirtue@gmail.com, bbn_galahad
	- BBN - where to find iso for MS Office: https://www.d.bbn.com/Software/Microsoft/
	- If the assembler fails to put the application onto a Virtue, chances are that there wasn't enough space on the Virtue.  The output won't really tell you that though.  Try pulling/starting the container manually:
		- Run `docker-virtue/virtue/get_docker_login_command.sh`, then copy/paste and run the `docker login` command it gives you.
		- `sudo docker pull 703915126451.dkr.ecr.us-east-2.amazonaws.com/starlab-virtue:IMAGE_NAME` (note that the image name comes from the same `VirtueDockerConf.yaml` file, usually it's `virtue-CONTAINERNAME`)
	- Any Windows application docker image requires the 8GB Virtue.
	- Crossover licenses are checked into the BBN repo (but also probably are copied elsewhere).
- Office:
	- Last I checked, `docker pull` freezes for some reason when pulling down our Office docker images.  This is a known problem for docker, but I didn't find a solution.  There was definitely enough disk space on the host system.
	- Try running Office on a "Virtue" that doesn't have any of the LSM, kernel modules, extra services, etc.  I think that helped somewhat, but don't know more.  One possibility is that there's so much logging that it's slowing down the system - not sure.
	- Upgrading the XPRA version improved Office performance, so maybe they'll improve it even more.
	- Using the "safe version" of Word (`winword.exe /safe`) didn't help at all.
	- Mounting the Office ISO, on a Virtue (outside docker):
		- Pull down the ISO from https://www.d.bbn.com/Software/Microsoft/
		- `mkdir msoffice2013`
		- `sudo mount -o loop /home/virtue/msoffice.ISO msoffice2013`
		- Add directory (not iso) to docker volume for office-prep's container.
		- Start the container.
		- (This is also in the `docker-virtue` repo under `virtue/README.md`, under "Updating Containers".)
- Keys:
	- Generating keys:
	```
	# Generate a private key
	openssl genpkey -algorithm rsa -pkeyopt rsa_keygen_bits:2048 -out virtue_1_key.pem
	
	# Generate a public key from the private key
	openssl rsa -in virtue_1_key.pem -pubout -out virtue_1_pub.pem
	```
	- rethinkdb.pem - RethinkDB's private key
	- rethinkdb_cert.pem - cert created from RethinkDB's private key
	- excalibur_key.pem - private key for Excalibur (for signing things)
	- excalibur_pub.pem - public key for Excalibur (for checking signature on the Virtue side)
	- virtue_1_key.pem - private key for a Virtue
	- virtue_1_pub.pem - public key for a Virtue
	- Note that ultimately EACH Virtue should have its own private/public key pair!  (Currently does not.)
	- Key locations:
		- On Excalibur server:
			- rethinkdb_cert.pem
			- `virtue_*_pub.pem` - for each virtue that is up (* = Virtue ID)
			- excalibur_key.pem
		- On Virtue:
			- virtue_[VIRTUE_ID]_key.pem
			- excalibur_pub.pem
			- rethinkdb_cert.pem
- How to get to Kibana:
	- `ssh -i ~/.ssh/starlab-virtue-te.pem -L 5601:127.0.0.1:5601 -N ubuntu@AGGREGATOR_IP`
	- In a local browser, go to `localhost:5601`
	- Credentials are admin/admin
- How to get to Blue Force Tracker (BFT):
	- `ssh -i ~/.ssh/starlab-virtue-te.pem -L 3000:127.0.0.1:3000 -N ubuntu@EXCALIBUR_IP`
	- In a local browser, go to `localhost:3000`
	- You may need to install this browser extension:
		- https://chrome.google.com/webstore/detail/allow-control-allow-origi/nlfbmbojpeacfghkpbjhddihlkkiljbi?hl=en
		- https://addons.mozilla.org/en-US/firefox/addon/access-control-allow-origin/
		- Other browsers - search for a plugin that allow CORS (cross origin requests)
- The API doesn't make much sense about `startingTransducerIds` for a Role vs `startEnabled` for a Transducer.  In any case, our implementation just pays attention to `startingTransducerIds`.
- If you have to recompile the kernel:
	- The current deb files live in `galahad/unity/latest-debs`
	- If you have a machine that can run a KVM machine, follow the instructions in `unity/README.md`.
	- If not:
		- Create a VM (probably will work in an EC2 Instance too) of Ubuntu.
		- Clone `galahad/unity` on it and `cd` into it.
		- Install docker.
		- Clone `git@github.com:starlab-io/galahad-lsm` somewhere.
		- Run: `VERSION=4.13.0-46-generic CODENAME=artful LSM=[path to cloned LSM patches] ./containerize.sh ./helpers/build-kernel` (Note that this takes several hours.)
		- Copy the relevant compiled debs from `kernel-source` into `latest-debs` and commit.
	- If you have to actually edit the LSM:
		- Pull down the linux kernel (specifically Ubuntu's version 4.13.0-46-generic, or the next closest version if that no longer exists).
		- Apply the existing LSM patches (as when building the kernel in the above instructions).
		- Most of the interesting code is in: `<cloned linux kernel dir>/security/virtue/virtue_lsm.c`
		- If you want to add more hooks, write a handler function for it and call `LSM_HOOK_INIT()` on that (see existing examples in code).
		- Once you test and compile, create a git commit, export it as a patch (`git format-patch -1 HEAD`), and commit it to the galahad-lsm repo.
	- Here are a bunch of resources about writing LSMs and compiling the kernel:
		- https://www.kernel.org/doc/html/v4.10/process/howto.html
		- https://github.com/torvalds/linux/tree/v4.13
		- https://medium.freecodecamp.org/building-and-installing-the-latest-linux-kernel-from-source-6d8df5345980
		- http://www.linuxjournal.com/article/6279
		- https://thibaut.sautereau.fr/2017/06/02/linux-security-modules-part-2/
		- http://blog.ptsecurity.com/2012/09/writing-linux-security-module.html
- If you have to edit the Windows/Crossover logs:
	- https://github.com/starlab-io/galahad-wine
	- Install docker.  Follow the readme.  Basically just run `./build-wine.sh`.
	- To add some new logging, first find the event that you want to log.  Try looking in `ext-sources/wine/dlls/kernel32/`, `ext-sources/wine/dlls/ws2_32/`, `ext-sources/wine/server/`, or just `grep`ing the source tree.  In that file, `#include <syslog.h>` and add a call to `syslog()` to record the event.  Follow the examples from previous commits - you want to log in a "key1: value1 key2: value2" format.  Include any information you can find about the event, e.g. we definitely want a PID (or even better, process name) if at all possible.
	- Add the compiled versions of the files you modified into `grab_stuff.py`.  Run `./grab_stuff.py`.
	- To test, start up a Unity with a Windows Virtue on it (e.g., wincmd) and ssh to the Unity.  If that's not automated, then follow the instructions further down about starting up a Virtue directly from `docker-virtue`.
		- Copy into the docker container the `cxoffice-overlay.tgz` file that `grab_stuff.py` gave you, as well as `install_overlay.py`: `sudo docker cp <local file> wincmd:.`
		- Exec into the docker container: `sudo docker exec -ti wincmd bash`
		- Install the overlay: `./install_overlay.py`
		- Kill XPRA/Crossover if it's running and start it again: `./kickoff.sh` or `xpra start --bind-tcp=0.0.0.0:2023 --html=on --start-child="/opt/cxoffice/bin/cxsetup"` (This will start the default Crossover screen, not a specific application.  From here you can install an application or just create a bottle and use the built-in apps.)
	- The official build is via the Jenkins job: `http://35.170.157.4:8080/view/all/job/virtue-wine/`
	- Once `virtue-wine` is done, also run `docker-virtue`, which will take the files generated in `virtue-wine` and incorporate them into the docker images. `http://35.170.157.4:8080/view/all/job/docker-virtue/`


## Where things live (that I've either worked on or found helpful for debugging; Ctrl-F is your friend for this list):

- `galahad/assembler/payload` - any (potentially compiled) objects that must be installed on a Virtue: syslog-ng config, syslog-ng transducer module, some elasticsearch certs, auditd rules, the net_block actuator deb file, etc.  Make sure to update these if one of the underlying things changes!  We always forget.
- `galahad/assembler/stages` - setup scripts related to specific components of a Virtue
- `galahad/deploy` - all the scripts to set up a stack / all the machines on a stack (except for a Virtue)
- `galahad/excalibur/website`
	- `apiendpoint_security.py` - the thing that actually sends commands to RethinkDB
	- `routes/virtue.py` - wrappers that catch the HTTP requests and forward them to the actual API endpoints
	- `services/errorcodes.py` - list of error codes as defined by APL's API
	- `start-screen.sh` - starts the `screen` session that runs Excalibur - useful if you need to restart Excalibur
	- `.excalibur` - config file for Excalibur (specifically, the security API endpoint and the heartbeat listener)
- `galahad/tests/integration` - specifically `test_security_api.py`, can be run on Excalibur with `pytest test_security_api.py`.  Any method whose name starts with "test_" will be run as a test.  Note that the security tests start up a Virtue, run the tests, and shut down the Virtue.  So the first test takes a long time to run.
- `galahad/transducers`
	- `actuators/networkactuator` - Zach's network blocker actuator
	- `docker` - unused
	- `filter` - unused
	- `listener`, `merlin`, `processkiller` - everything needed to build debs for these services
	- `syslog-ng-config` - as it says on the tin, however, compare with `galahad/assembler/payload` - not sure which is used
	- `transducer-module` - Jon's syslog-ng module that filters transducer messages
	- `build_deb.sh`, `build_merlin.sh`, `install_heartbeatlistener.sh`, `syslog-ng-module-setup.sh`, `syslog-ng-server-setup.sh` - files related to building/installing
		- Most (?) of the deb files get rebuilt automatically when the stack is built (when a Virtue is created?), but it seems that at least the ProcessKiller doesn't.
	- `merlin.py`, `listener.py`, `processkiller.py` - transducer-related services
	- `print_db.py` - script to print everything in RethinkDB.  Use the attached one instead.
- `galahad/unity` - all the scripts for rebuilding the kernel, deb files are in `latest-debs` (pretty sure we don't actually need all 8 of those)
- `docker-virtue/virtue` (by the way, `docker-virtue` is a public repo)
	- `app-containers` - Dockerfiles for all apps, as well as apparmor and seccomp policies
	- `virtue-base` - base Dockerfile, also the kickoff.sh script that starts up XPRA
	- `VirtueDockerConf.yaml` - info about all applications/containers - mapping between app name, image name, port, and apparmor/seccomp policies
	- `build.py`, `run.py`, `publish.py` - scripts for various Virtue docker operations
	- You definitely want to read the README in this repo
- `galahad-wine`
	- `ext-sources/wine` - all the wine source
	- `build-wine.sh`, `grab_stuff.py`, `install_overlay.py` - files for building/installing the modified Wine into Crossover
- `galahad-lsm` - a set of patches that go on top of the ubuntu 4.13.0-46-generic kernel source code.  These are patches because the linux kernel is MASSIVE.  There are scripts to apply these in `galahad/unity`.
- `galahad-config` - keys for various things

