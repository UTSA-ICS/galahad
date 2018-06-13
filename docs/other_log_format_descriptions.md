# App Armor log format

All app armor log entries start with 

	audit(...)

This is followed by a collection of key-value pairs.  An example app armor log is 

	Jun 13 16:18:07 ip-172-30-95-82 kernel: audit: type=1400 audit(1528906687.621:20): apparmor="DENIED" operation="ptrace" profile="docker_chrome" pid=20408 comm="TaskSchedulerBa" requested_mask="trace" denied_mask="trace" peer="docker_chrome"

Here, the app armor policy is denying a ptrace call.  The keys have the following meanings

* apparmor - ALLOWED/DENIED, AppArmor's action on the operation
* operation - The operation AppArmor processed (ptrace in this case, could be file open, etc)
* profile - The profile that AppArmor used to apply this action
* name - The file/object that the operation was attempted on.  This is not applicable here, but would be included for things like file operations
* pid - The PID of the process attempting the operation 
* comm - The command/name of the process attempting the operation
* requested_mask - What was wanted to do with the operation (trace in this case, could be 'r' for a file open operation)
* denied_mask - What AppArmor allowed/prevented the process from doing
* peer - Specific to ptrace

AppArmor doesn't appear to be the best about explaining their log messages, so I don't have any good additional sources to give you.  

# SSHD Log format

Most of the sshd logs take the following form:

	[EVENT] for [USER] from [SOURCE] [SSH_INFO]

Where source is of the form

	[IP] port [PORT] 


And SSH_INFO can be of the form

	ssh2
	ssh2: RSA SHA256:LI/TSnwoLryuYisAnNEIedVBXwl/XsrXjli9Qw9SmwI
	ssh2: RSA e8:31:68:c7:01:2d:25:20:36:8f:50:5d:f9:ee:70:4c

Examples include:

	Mar 14 19:50:59 server sshd[18884]: Accepted password for fred from 192.0.2.60 port 6647 ssh2
	Mar 14 19:52:04 server sshd[5197]: Accepted publickey for fred from 192.0.2.60 port 59915 ssh2: RSA SHA256:5xyQ+PG1Z3CIiShclJ2iNya5TOdKDgE/HrOXr21IdOo
	Jan 28 11:52:05 server sshd[1003]: Accepted publickey for fred from 192.0.2.60 port 20042 ssh2
	Mar 14 20:14:18 server internal-sftp[11581]: session opened for local user fred from [192.0.2.60]


	Mar 19 11:11:06 server sshd[54798]: Failed password for root from 122.121.51.193 port 59928 ssh2
	Mar 19 11:11:10 server sshd[54798]: error: maximum authentication attempts exceeded for root from 122.121.51.193 port 59928 ssh2 [preauth]
	Mar 19 11:11:10 server sshd[54798]: Disconnecting authenticating user root 122.121.51.193 port 59928: Too many authentication failures [preauth]

More details here https://en.wikibooks.org/wiki/OpenSSH/Logging_and_Troubleshooting
