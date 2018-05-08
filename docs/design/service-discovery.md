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

## PROPOSED APPROACH: Use Route53 with a private namespace

This can be managed from within CloudFormation scripts (see also `virtue-stack-svc-disco.yaml`):

### Add a Hosted Zone

Docs: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-route53-hostedzone.html

```yaml
VirtueHostedZone:
    Type: 'AWS::Route53::HostedZone'
    Properties: 
      HostedZoneConfig:
        Comment: "VPC-private zone for service discovery"
      HostedZoneTags:
        - Key: Project
          Value: Virtue
        - Key: Name
          Value: !Join 
            - ''
            - - VirtUE-
              - !Ref NameSuffix
              - '-Zone'
      Name: 'galahad.test'
      VPCs:
        - VPCId: !Ref VirtUEVPC
          VPCRegion: !Ref "AWS::Region"
```

### Add a RecordSet or RecordSetGroup for each service

A `RecordSet` is a single DNS record. Note that the `HostedZoneName` must match the name in the `HostedZone`. 

Docs: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-route53-recordset.html

For example:

```yaml
  RethinkDBDNSRecord:
    Type: 'AWS::Route53::RecordSet'
    Properties: 
      HostedZoneName: galahad.test.
      Name: rethinkdb.galahad.test.
      Type: A
      TTL: '900'
      ResourceRecords:
        - !GetAtt GalahadRethinkDB.PrivateIp
```

A `RecordSetGroup` is a record for a set of clustered instances of a service. These can be chosen from in a variety of ways, including weighted random selection, geolocation, etc.

Docs: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-route53-recordsetgroup.html

```yaml
  AggregatorRecordSet:
    Type: 'AWS::Route53::RecordSetGroup'
    Properties:
      Comment: 'Randomly select from three Aggregator instances'
      HostedZoneName: galahad.test.
      RecordSets:
        - Type: 'AWS::Route53::RecordSet'
          Properties:
            HostedZoneName: galahad.test.
            Name: aggregator.galahad.test.
            Type: CNAME
            TTL: '900'
            SetIdentifier: 'Aggregator One'
            Weight: 10
            ResourceRecords:
              - !GetAtt AggregatorInstanceOne.PrivateIp
        - Type: 'AWS::Route53::RecordSet'
          Properties:
            HostedZoneName: galahad.test.
            Name: aggregator.galahad.test.
            Type: CNAME
            TTL: '900'
            SetIdentifier: 'Aggregator Two'
            Weight: 10
            ResourceRecords:
              - !GetAtt AggregatorInstanceTwo.PrivateIp
```

Since these have equal weights, the likelihood of returning each is the same. There are a handful of ways to control routing, including by region, by geolocation, etc. For more info, see here: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html