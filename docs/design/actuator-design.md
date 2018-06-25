# Actuators

## Overview

Actuators are a type of transducer.  We will largely reuse the existing Merlin framework.

## Overall lifecycle of an actuator (an example)

- User asks the API to enable a transducer (actuator) that will kill processes called "evilprocess" on a particular Virtue.
- API puts the user's request into RethinkDB.
- On the specified Virtue, Merlin receives the message through RethinkDB.
- Merlin does two things:
    - Runs a process that immediately kills running processes called "evilprocess" and logs what it killed.
    - Forwards the message (kill "evilprocess") to a unix socket.
- The Virtue LSM gets a message and adds "evilprocess" to its list of blocked processes. If it sees a process called "evilprocess" begin to launch, it will prevent it from starting and log this event.
- If the user decides that "evilprocess" should no longer be blocked, they would disable the actuator or change its configuration.

In this way, both existing and future "evilprocess" processes will be killed. The same idea can be applied to blocking ports.

## Excalibur -> RethinkDB -> Merlin

- We will reuse the same table in RethinkDB as we used for the sensor transducers, since sensors and actuators require the same data.  Actuators will have more data in their configuration but that should be parsed in Merlin, not at the Excalibur API level.
- This will require adding a "type" field (sensor vs actuator) so that Merlin can decide where to forward the message, as well as potentially other fields.  
- This table may or may not be later merged with the table used to signal Valor migration.
- The transducer's configuration will now be important.  
    - Enabling a transducer requires specifying the Virtue and the configuration, so each Virtue may have a different configuration for each transducer.
    - There will be only one actuator for each event type (kill process, block port, etc).  
    - The configuration will include a list of the affected items: processes to kill, ports to block, etc.  
    - If a user wants to add or remove an item from this list, they will re-enable the actuator via the API with a different configuration.  
    - We can provide convenience methods later so that someone won't accidentally delete the rest of the list.
    - The reason we shouldn't create multiple actuators of the same event type (for example, one for killing "evilprocess", another for killing "maliciousprocess", etc) is that we need to have a predefined list of transducers for the rest of the API to make sense.

## Things to do

- [ ] Accept actuator messages in the API
- [ ] Add API-RethinkDB-Merlin pipeline for actuators
- [ ] Implement the "immediate process kill" component
- [ ] Implement a method of communication between Merlin and the LSM
- [ ] Block processes in LSM that were communicated through the unix socket
- [ ] Log actions taken by each actuator
- [ ] (?) Heartbeat functionality
- [ ] Port blocking actuator - the block functionality itself, and listening for messages from Merlin
- [ ] Other actuators

## Additional decisions to make

- Should any actuators be enabled by default in a Virtue?

