# Blue Force Tracker Back-End

## Setup

Check out this directory to Excalibur or the Aggregator.

Run `./setup.sh`

You may need to add the "add-host" arguments to the `docker run` call if the DNS entries aren't passed into the docker container (see commented out lines in setup.sh).

## Running

The setup script will start the docker container as well.

TODO: Add docker-compose.yml file

If you are developing, it may be easier to simply run a `node` container and volume in the src and galahad-config directories separately, so that your code changes are saved to your host.

## Interacting

### Checking connectivity

Run from your host:

```
curl -X GET localhost:3000
```

This should return "Hello World!"

### Access in a browser

On your local machine, run:

```
ssh -i ~/.ssh/starlab-virtue-te.pem -L 3000:127.0.0.1:3000 -N ubuntu@[IP of Aggregator / host where docker is running]

```

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

