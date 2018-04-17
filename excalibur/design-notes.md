# Design Notes

## Transducers Data Model

- From the API docs: "A `transducer` is a security component that either passively monitors offline Virtue data (sensor) or actively monitors and can modify inline data (actuator)."
	- This definition is wonky: what about passive inline sensors?
	- I think they are trying to be overly scientific by using fancy words, and really just mean "sensors and actuators"
- API docs give transducers a small number of properties:
	- `id` (string) The unique identifier for this Transducer. Format is implementation-specific. Must be unique across all instances.
	- `name` (string) A human-readable name for this Transducer. 
	- `type` (string) (enum) The type of Transducer. SENSORs passively monitor offline Virtue data; ACTUATORs actively monitor and can modify inline data. Enum Values: [SENSOR, ACTUATOR]
	- `startEnabled` (boolean) When a new Virtue is instantiated, this flag controls whether this Transducer should be enabled by default. This is in addition to the Transducers that are automatically enabled by the Virtue's Role specification.
	- `startingConfiguration` (object) When a new Virtue is instantiated, this is the starting configuration that should be applied. Format is Transducer-specific.
	- `requiredAccess` (list of string) What access to underlying resources this Transducer needs. Enum Values: [NETWORK, DISK, MEMORY]
- Some of these properties are per-instance of a transducer, and some are per-class of a transducer.
	- Per Instance
		- `id`
		- `name`
		- class (implied)
		- `currentConfiguration` (implied)
	- Per Class 
		- `type`
		- `startEnabled`
		- `startingConfiguration`
		- `requiredAccess`

Objects I think we'll need:

```json

TransducerClass {

	"className": "TransducerClass",
	"type": ["SENSOR", "ACTUATOR"],
	"startEnabled": [ true, false ],
	"startingConfiguration": { /*...*/ },
	"requiredAccess": [ "NETWORK", "DISK", "MEMORY" ]
}

VirtueInstance {

	/* ... */
	"id": "uuid-for-instance"
	/* ... */
}

TransducerInstance {

	"id": "uuid-for-instance",
	"name": "human-readable-name",
	"virtueId": "virtue-this-transducer-is-running-on",
	"transducerId": "some TransducerClass className",
	"enabled": [ true, false ],
	"currentConfiguration": { /* ... */ }

}

TransducerConfig { /* ... */ }

```