# Description of log messages

path_mkdir - directory creation
	* `LogType: Virtue Event: path_mkdir Parent: '%s' Child: '%s' ProcName: '%s' PID: %d`
		* Parent: Path to parent directory (where this new directory is getting created)
		* Child: Name of new directory being created
		* ProcName: Name of process creating this directory
		* PID: PID of process creating this directory

bprm_set_creds - process start
	* `LogType: Virtue Event: bprm_set_creds Name: '%s' ParentName: '%s' ParentPID: %d`
		* Name: Name of process being launched
		* ParentName: Name of parent process launching this new process
		* ParentPID: PID of parent process launching this new process

task_create - thread start
	* `LogType: Virtue Event: task_create ParentName: '%s' ParentPID: %d`
		* ParentName: Name of parent process launching this new thread
		* ParentPID: PID of parent process launching this new thread

task_alloc - thread allocation (more or less the same as thread start)
	* `LogType: Virtue Event: task_alloc Name: '%s' [PID: %d]`
		* Name: Name of parent process launching this new thread
		* PID: PID of parent process launching this new thread [if available]

inode_create - file write
	* `LogType: Virtue Event: inode_create Path: '%s' ProcName: '%s' PID: %d`
		* Path: Path to file that is being written
		* ProcName: Name of process writing to this file
		* PID: PID of process writing to this file

socket_connect - socket connect
	* `LogType: Virtue Event: socket_connect Family: %s Addr: '%s' [Port: %d] ProcName: '%s' PID: %d`
		* Family: Type of socket (IPV4, IPV6, Unix, or a number corresponding to the family type)
		* Addr: Address of socket that is being connected to
		* Port: Port that socket is being connected to [for IPV4 and IPV6 only]
		* ProcName: Name of process connecting this socket
		* PID: PID of process connecting this socket

socket_bind - socket bind
	* `LogType: Virtue Event: socket_bind Family: %s Addr: '%s' [Port: %d] ProcName: '%s' PID: %d`
		* Family: Type of socket (IPV4, IPV6, Unix, or a number corresponding to the family type)
		* Addr: Address of socket that is being bound to
		* Port: Port that socket is being bound to [for IPV4 and IPV6 only]
		* ProcName: Name of process binding this socket
		* PID: PID of process binding this socket


# Windows Compatibility Layer Log Messages

socket_accept - socket accept
	* `Event: socket_accept Socket: 0x%04lx PID: %d`
		* Socket: ID of socket
		* PID: PID of process accepting on socket 
		
socket_bind - socket bind
	* `Event: socket_bind Socket: 0x%04lx [Addr: '%s',] [Port: %d] [IPXSocket: %d] [ServiceName: '%s'] PID: %d`
		* Socket: ID of socket
		* Addr: IP address of socket that is being connected to
		* Port: Port of socket that is being connected to [only for AF_INET and AF_INET6]
		* IPXSocket: Socket connection data for IPX sockets [only for IPX sockets]
		* ServiceName: IRDA service name [only for AF_IRDA]
		* PID: PID of process binding on socket
		
socket_connect - socket connect
	* `Event: socket_connect Family: %s, [Addr: '%s',] [Port: %d] [IPXSocket: %d] [ServiceName: '%s'] PID: %d`
		* Family: AF_INET, AF_INET6, AF_IPX, AF_IRDA, or other ID
		* Addr: IP address of socket that is being connected to
		* Port: Port of socket that is being connected to [only for AF_INET and AF_INET6]
		* IPXSocket: Socket connection data for IPX sockets [only for IPX sockets]
		* ServiceName: IRDA service name [only for AF_IRDA]
		* PID: PID of process connecting with this socket

socket_listen - socket listen
	* `Event: socket_listen Socket: 0x%04lx PID: %d`
		* Socket: ID of socket that is listening
		* PID: PID of process listening on this socket

create_process - process creation
	* `Event: create_process caller_pid: "%d" cmd_line: "%s"`
		* caller_pid: PID of caller process
		* cmd_line: Command line that was used to start/create the process

process_start - process start
	* `Event: process_start new_wpid: %d cmd_line: "%s"`
		* new_wpid: PID of new process
		* cmd_line: Command line that was used to start/create the process

process_died - process death
	* `Event: process_died wpid: %d`
		* wpid: PID of process that died

srv_create_proc - create process
	* `Event: srv_create_proc new_wpid: %d new_upid: %d parent_wpid: %d`
		* new_wpid: PID of process that has been created
		* new_upid: Unix PID of process that has been created
		* parent_wpid: PID of caller process

open_fd - file open
	* `Event: open_fd File: "%s" Exe: "%s" wpid: %d`
		* File: Path to file that is being opened
		* Exe: Name of process that is opening the file
		* wpid: PID of process that is opening the file
