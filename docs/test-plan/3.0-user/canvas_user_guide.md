# Canvas usage instructores

VNC into the Canvas instance on your stack.  VNC Viewer (https://www.realvnc.com/en/connect/download/viewer/) works fine.

In your VNC client, set up a connection to the Canvas instance on your stack.  VNC is broadcasting on port 1, so you'll set your connection address as

	xxx.xxx.xxx.xxx:1

and connect.  It should alert you it's an unencrypted connection; this is fine for now.  It will prompt you for a password, the password is 

	canvas4U

Once you have connected to the instance, confirm canvas will start by running 

	./start_canvas.sh

If it does, great!  Close it and let's set up some configuration.

Open firefox (on the Canvas VNC), and navigate to 

	excalibur.galahad.com:5002

This will fail.  

There is now an output.js, in that file go in and find a commented out line

	// window.open("http://canvas.com:3000/connect/excalibur")

Uncomment this out. Rerun canvas with 

	./start_canvas.sh

Log in with the account
	
	jmitchell@virtue.gov
	Test123!

Open the firefox app (if availabile).  This should open an XPRA session for the firefox virtue

If this is a blank orange screen, something may be wrong with the Virtue or Docker container.  Using the admin CLI, run 

	ubuntu@ip-172-30-1-44:~/galahad/excalibur/cli$ ./virtue-admin user virtue list --username=jmitchell
	[
	    {
	        "applicationIds": [],
	        "id": "Virtue_firefox123_1546984484",
	        "ipAddress": "10.91.0.2",
	        "resourceIds": [],
	        "roleId": "firefox1231546885862",
	        "state": "RUNNING",
	        "transducerIds": [],
	        "username": "jmitchell"
	    }
	]

SSH into the IP given in the above output for firefox123 from excalibur, then pull up a shell in the docker container

	sudo docker exec -ti firefox bash

Then, ps for the xpra session

	ps aux | grep xpra

And kill this session.  Then run

	./kickoff.sh

To restart the service.  You can safely ignore warnings about the .xpra directory already existing. 

Ideally this should work!  If it doesnt, ask Mark or Farhan or Jon, and update the guide to reflect corrects.  Good luck.  