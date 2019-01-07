# Blue Force Tracker Back-End

## Setup

This will get installed by default onto a stack.

You can also run this separately in a docker container.  To do that, check out this directory to Excalibur or another machine on the stack.  Run `./setup.sh`

You may need to add the "add-host" arguments to the `docker run` call if the DNS entries aren't passed into the docker container (see commented out lines in setup.sh).

## Running

If the system was installed via the default stack creation process, the BFT will already be running.  It can be controlled with `systemctl`, e.g.: `sudo systemctl start bft`.

If running manually with `./setup.sh`, the setup script will start the docker container as well.

If you are developing and using docker, it may be easier to simply run a `node` container and volume in the src and galahad-config directories separately, so that your code changes are saved to your host.

## Interacting

### Access in a browser

On your local machine, run:

```
ssh -i ~/.ssh/starlab-virtue-te.pem -L 3000:127.0.0.1:3000 -N ubuntu@[IP of Excalibur / host where node is running]

```
You can then access the BFT by going to `localhost:3000` in your local machine's browser.


### Functionality

```
/number_messages

    Number of messages in the current index

/all_messages

    "All" messages in the current index (probably there's a limit on how many are returned)

/messages_per_virtue/:timerange

    timerange: "hour" or "day"

    Number of ES messages, grouped by Virtue ID

/messages_per_virtue_per_type/:timerange

    timerange: "hour" or "day"

    Number of ES messages, grouped by Virtue ID and Event

/messages_per_type/:virtueid/:timerange

    virtueid: Virtue ID string

    timerange: "hour" or "day"

    Number of ES messages for a specific Virtue ID, grouped by Event

/virtues_per_valor

    Number of virtues per valor

/migrations_per_virtue

    Number of times each Virtue has migrated

/virtues_per_role

    Number of Virtues in each role (if 0, role isn't included)



/valors

/virtues

/roles

/users

/transducers

/applications

/resources



/transducer_state

    Current state of transducers on each Virtue

```

