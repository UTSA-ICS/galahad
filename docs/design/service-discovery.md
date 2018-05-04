# Service Discovery

Things that need to be discovered:

- elasticsearch
- rethinkdb
- kibana
- excalibur
- Valor/Unity instances?
    - Probably not, as we have to manage them through LDAP anyway

## AWS Route 53

1. Create a private (VPC-internal) namespace
2. Create a `service`. Needs:
    a. Name
    b. DNS settings (records, routing policy: multivalue or weighted)
    c. Health check (public namespaces only, so we can't use)
3. Register instances as they boot
4. Deregister instances if they die
5. Deregister the namespace when it is not needed

Thoughts:

- PRO: Easy, integrated with AWS
- PRO: Would work well for ES, Rethink, etc.
- PRO: Integrates well with CloudFormation
- CON: Can't use integrated health checks, since we're using a private namespace
- CON: Need to have the AWS API key, so can't do it from inside the EC2 instance

## LDAP

- Already have to use it for other stuff
- Harder to interact with programmatically?

## Standalone Tools

Dated, but probably still more or less accurate, from what I can tell: https://technologyconversations.com/2015/09/08/service-discovery-zookeeper-vs-etcd-vs-consul/ 

- ZooKeeper: requires Java ==> :non-potable-water:
- etcd: http-accessible key/value store. Needs other stuff to help it for service disco
- Registrator: automatically registers/deregs docker containers as they start and stop
- consul: gossip-based strongly consistent KV store w/ DNS and HTTP-based interfaces
    - Well regarded in the community
    - Seems to be the preferred technique when not using a full orchestration system

## PROPOSED APPROACH

- Use Route53 with a private namespace
- Consul would be nice, especially the health checks