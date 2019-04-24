# Canvas usage instructions

VNC into the Canvas instance on your stack. VNC Viewer (https://www.realvnc.com/en/connect/download/viewer/) works fine.

In your VNC client, set up a connection to the Canvas instance on your stack. VNC is broadcasting on port 1, so you'll set your connection address as

	xxx.xxx.xxx.xxx:1

It should alert you it's an unencrypted connection; this is fine for now. It will prompt you for a password, which is `canvas4U`.

Open a terminal and go to `~/galahad/canvas/`
Setup the oauth app ID and private key, as well as some dependencies, with `setup_canvas.sh`. (Part of this needs to be built into canvas at some point)

	./setup_canvas.sh jmitchell@virtue.gov Test123!

Then run canvas with `start_canvas.sh`.
Log in with the account

	jmitchell@virtue.gov
	Test123!

Open the firefox app (if availabile). This should open an XPRA session for the firefox virtue.

If this is a blank orange screen, something may be wrong with the Virtue or Docker container. Using the user CLI, run

	ubuntu@ip-172-30-1-44:~/galahad/excalibur/cli$ ./virtue user virtue list
	[
	    {
	        "applicationIds": [],
	        "id": "Virtue_firefox123_1546984484",
	        "ipAddress": "10.91.0.xyz",
	        "resourceIds": [],
	        "roleId": "firefox1231546885862",
	        "state": "RUNNING",
	        "transducerIds": [],
	        "username": "jmitchell"
	    }
	]

SSH into the virtue given in the above output, then open a shell in the docker container

	sudo docker exec -ti firefox bash

Then, kill the xpra session. You can find the pid with

	ps aux | grep xpra

Then run

	./kickoff.sh

To restart xpra. You can safely ignore warnings about the .xpra directory already existing.

If this doesnt work, ask Mark, Farhan, or Jon, and please update this guide to reflect changes.
