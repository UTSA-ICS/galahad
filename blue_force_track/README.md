# Blue Force Tracker

This readme covers the Excalibur Blue Force Tracker (BFT), what it does, its design, and how to build it, make changes to it, and deploy it.  

## What It Does

The BFT exists to provide a simplistic, useful dashboard overview of the state of a Galahad deployment.  This currently focuses on the state of valors, virtues, roles, applications, users, and resources.  The goal is that a user should be able to, at a glance, understand the load, application, and security contexts of the system.  

## How to Use It 

Currently, the BFT is automatically deployed and started on the Excalibur instance of a galahad stack.  It can be run manaually by navigating to galahad/blue_force_track/back_end/src and calling 

	node index.js

This will start the BFT backend, which will serve the front frontend and handle REST API calls on port 3000.  

### Security

The BFT as a webapp is in no way secured; there is no HTTPS or authentication capability in it at the present time.  The BFT should only ever be deployed to a port that is not publically accessible.  Users should SSH into the excalibur instance, and SSH tunnel the BFT port back to their local environment to provide a secured session.

## Design 

The back end for the BFT is a simple node.js application that both serves the front end of the application, and provides REST API calls for the front end to gather data from.  The back end resides at galahad/blue_force_track/back_end/src/index.js, and all changes for it can take place in this file.  The back end queries RethinkDB, LDAP, and Elasticsearch to provide data; any changes in any of these sources will require changes to the index.js to compenstate.  

The front end is a TypeScript application leveraging the Angular framework.  It uses PrimeNg and bootstrap for dashboarding, and D3.js Angular components for graphs.  To be served by the frontend, it must be compiled down to raw JavaScript (details here below).  


## Requirements

The frontend requires Node.js (https://nodejs.org/en/), along with the requirements from the package.json file in back_end/src.  Run 

	npm install

after installing node to have npm get these for you.

The front end requires Angular (https://angular.io/).  It also has package requirements to npm install in it's package.json as well.  Running 

	npm install 

in front_end/blue-force-track/ should require the correct version of angular and all other requirements.  

## Deployment

The backend requires no additional steps to deploy (besides npm installing the requirements via package.json file).  

The front end must be deployed in order to be served by the backend.  To do this, navigate to galahad/blue_force_track/front_end/blue-force-track/ and run 

	ng build --prod 

This will compile the TypeScript application down into raw JS and place it in the blue-force-track/dist directory; copy over all files from here into galahd/blue_force_track/back_end/src/front_end/ directory to finish deployment. 

## Development

All changes to the backend can be made in the index.js file.  Running 

	node index.js 

Will run the backend; all console messages will appear in this terminal.  

The front end is more complex; for development, you will likely be touching code in galahad/blue_force_track/front_end/blue-force-track/src/app/.  

To update the front ends API queries to the back end, see services/data.service.ts.  Note that the URL of the backend is hard coded as localhost:3000 in this file; this is poor implementation and should be fixed.  

To update any of the dashboards, see the views/ directory.  You should only need to touch the .html and component.ts file to make most changes. 

To add an additional dashboard, you'll need to create a new view and ensure it's specified in the menuItems object in app.component.ts and it's route to app.routes.ts 

To run a development/debug deployment of the frontend, in galahad/blue_force_track/front_end/blue-force-track/, run 
	
	ng serve


To make this work with the backend, you will need to SSH tunnel to an excalibur instance running the backend.  