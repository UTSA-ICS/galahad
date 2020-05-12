# Galahad: introduction

Galahad is Star Lab's solution to IARPRA's VirtUE program. The
following is from the proposal; see that document for more
details. Note that this project depends on another github project
called valor. That project holds the Valor component seperately to
simplify testing.

Galahad, a revolutionary user computer environment (UCE) for the
Amazon Cloud that is designed to be highly interactive while
mitigating legacy and cloud-specific threats. Galahad meets all 11
requirements called out in IARPA-BAA-16-12, addressing the broad areas
of threat mitigation, sensing and logging, lifecycle management and
control, user interaction, and cost and performance.  Unique to the
VirtUE program is the requirement that a defensible interactive UCE be
built on top of a completely untrusted computing foundation, namely
Amazon Web Services (AWS).


Star Lab’s Galahad takes a holistic approach to creating a secure,
interactive UCE. Galahad leverages role-based isolation, attack
surface minimization practices, operating system (OS) and application
hardening techniques, real-time sensing, and maneuver / deception
approaches to reduce the risk associated with cloud
deployments. Galahad makes no attempt to establish trust, nor does it
require specialized, more costly services provided by AWS, e.g.,
dedicated servers.  Instead, Galahad impedes the ability of
adversaries to operate within the AWS by making it more difficult to
co-locate (either through the use of insiders, compromised
hypervisors, witting or unwitting peers, or remote access) with
targets, while also requiring adversaries consume more resources. Such
an increase in complexity and cost means Galahad also increases the
accuracy, rate, and speed with which threats are detected.


Galahad facilitates the construction, deployment, management, and
interfacing of role-based virtues. Star Lab’s virtues, consist
primarily of two components: Valor, a nested hypervisor and Unity, a
virtual machine running a small, hardened, de-privileged Linux
operating system (OS). Valor includes protections, sensors, and
virtual machine (VM) image authentication, but most importantly it
facilitates the regular, recurring live migration of Unity VMs. This
moving target defense approach deters hypervisor and peer VM threats
within AWS, an operating environment where trust can never be
completely established, by limiting the time an adversary has to
access targeted virtues while also increasing the number of access
points required by the adversary to be successful.

Unity includes additional protections to address external and insider
threats while also incorporating a compatibility layer for supporting
legacy Windows applications and adjustable sensors. Limiting Unity to
Linux (versus using Linux and Windows) allows Star Lab to more greatly
reduce the overall attack surface of the virtue, improve performance,
and streamline development. Additionally, executing Windows
applications on Linux increases the uncertainty, complexity, and cost
to the adversary.

Sensing and logging take place throughout the Galahad software stack,
without requiring modifications to the applications under
protection. Within Unity, these introspection points consist of kernel
instrumentation, activity monitors, and sensing points added to the
compatibility layer. Additional sensing and logging capabilities are
layered across Unity and Valor creating tripwires to detect adversary
tampering. Overall, a virtue’s protections and sensing capabilities
are adjustable, updatable, and collaborative, forcing adversaries to
navigate a well-covered attack surface to avoid
detection. Furthermore, the use of role-based virtues to reduce
behavior complexity boosts out-of-band analytics making Galahad a
highly defensible construct.


# Requirements

For reference, here are the requirements and how Galahad addresses
them:

1. **Interfacing with virtues within AWS** Galahad’s Virtue
Control API enables the lifecycle management of virtues, to include
their secure deployment into AWS.

2. **Immutable minimized virtues** Galahad’s Virtue Assembler
automates the creation of immutable, minimized virtues.

3. **Role-based virtues** All applications required for a role are
installed within a single Unity instance, which in turn executes
within a single instance of Valor.  Galahad maintains a 1:1 Unity to
Valor relationship.

4. **Defensible virtualized construct** Galahad’s Unity and Valor are
built with only required functionality, configured to reduce the
attack surface, and regularly migrated, addressing external, internal,
peer, and infrastructure threats.

5. **Virtue logging and adjustability** Galahad’s sensors span the
entire software stack and Galahad’s Log Digester filters logs based on
configurations and tasking received through Galahad’s Sensing and
Logging Control API.

6. **Dynamic virtue protections** Dynamic protections include live
migration, memory sanitization, and a stackable security policy

7. **Legacy application** Unity includes a compatibility layer
specifically designed to support legacy Windows applications.

8. **Information exchange** Galahad’s Virtue-Canvas API facilitates
the secure exchange of presentation information and enables resource
sharing.

9. **Virtue presentation interface** Galahad’s Canvas is a lightweight
application or webpage that presents the components necessary to
invoke and interact with applications running inside virtues.

10. **Virtue performance** Virtues have minimal inherent “must-have”
AWS requirements. Star Lab will use an AWS integrated test environment
to better refine instance configurations that effect cost and
performance.

11. **Virtue management** Inspired by Docker, Galahad’s Virtue
Assembler enables the easy transportation and extension of existing
virtues as well as the attestation of virtue creators.


# Tasks

The technical tasks are broken down as follows:

1.Virtue Construct Research and Development

1.1. Design and Develop Threat Mitigation Enablers

1.2. Integrate Application Support Enablers

2. Canvas Research and Development

2.1. Design and Develop Canvas Interface

2.2. Design and Develop Resource Sharing

3. Virtue Lifecycle Management Research and Development

3.1. Design and Develop Virtue Building and Packaging Tool

3.2. Design and Develop Virtue Control

4. Sensor and Logging Research and Development

4.1. Design and Develop a Sensor Suite

4.2. Design and Develop Sensor Control

5. System Testing and Experimentation

6. Technology Demonstration and Evaluation

7. Reporting and Management
