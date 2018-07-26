# `auditd` as a Galahad sensor

## Concept

`auditd` [1] is shorthand for the Linux Auditing System. It's a kernel facility used to audit a
variety of system events, from individual system call parameters all the way up to user login
or logout events. There are existing examples of auditd recipes to monitor what you'd need to
prove compliance with NISPOM, PCI/DSS, or STIG rules, as well as a large number of community-develped
rulesets [2], [3], [4] for auditing systems.

Inspired by the sshd event logging demonstrated at the midterm T&E event, we are exploring using 
auditd as a sensor. Since we're already picking up the events in `/var/log/auth`, we should be able
to pick up `/var/log/audit` without any real difficulty as well.

Alex J. tested this on a Unity machine, and it works, with some changes to syslog-ng:

```
source s_auditd {
        file(/var/log/audit/audit.log flags(no-parse));
};

parser p_auditd {
        linux-audit-parser (prefix(".auditd."));
};

log {
        source(s_auditd);
        parser(p_auditd);
        destination(d_file);
        destination(d_elastic);
        destination(d_network);
};
```

## Tasks for implementation

- [ ] Ensure auditd is installed and running (it's not by default)
- [ ] Experiment with auditd rules
- [ ] Determine how to control auditd ruleset at runtime using MERLIN
- [ ] Add ruleset injection to assembler process
- [ ] Integrate with remainer of system

## Notes

- Need to modify the transducer control system to handle audit messages
- Determine good set of audit rules - I like the ones in [3]
- Open question on whether the ruleset should be modifiable during runtime, or fixed. If fixed, you can't use the sensor control API to shut off auditd config, but then again, you can't shut it off, which is kinda important too.

## References

[1]: https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/6/html/security_guide/chap-system_auditing
[2]: https://github.com/linux-audit/audit-userspace/tree/master/rules
[3]: https://gist.github.com/Neo23x0/9fe88c0c5979e017a389b90fd19ddfee
[4]: https://github.com/gds-operations/puppet-auditd/pull/1