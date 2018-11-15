/*
 * VM monitor daemon
 * Copyright (c) Star Lab Corp. 2018.
 * All rights reserved.
 *
 * Author: Christopher Clark, Oct-Nov 2018
 */

#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>
#include <errno.h>
#include <stdbool.h>
#include <inttypes.h>
#include <signal.h>

#include <syslog.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>

#include <libvmi/libvmi.h>

#define dprintf printf

/* max length of pending connections: */
#define LISTEN_MAX_BACKLOG  8

#define MONITOR_LOG_IDENT   "VMmonitor"

int
list_processes(vmi_instance_t vmi, const char *target_vm_name)
{
    int rc = -1;
    do {
        unsigned long tasks_offset = 0, pid_offset = 0, name_offset = 0;
        addr_t list_head = 0, cur_list_entry = 0, next_list_entry = 0;

        if ( (VMI_FAILURE == vmi_get_offset(vmi, "linux_tasks", &tasks_offset))
          || (VMI_FAILURE == vmi_get_offset(vmi, "linux_pid", &pid_offset))
          || (VMI_FAILURE == vmi_get_offset(vmi, "linux_name", &name_offset)) )
        {
            syslog(LOG_ERR, "Failed to read offsets for VM: %s",
                   target_vm_name);
            break;
        }

        if ( VMI_FAILURE == vmi_translate_ksym2v(vmi, "init_task", &list_head) )
        {
            syslog(LOG_ERR, "Failed to translate init_task ksym for VM: %s",
                   target_vm_name);
            break;
        }

        list_head += tasks_offset;

        cur_list_entry = list_head;
        if ( VMI_FAILURE == vmi_read_addr_va(vmi, cur_list_entry, 0,
                                             &next_list_entry))
        {
            syslog(LOG_ERR, "Failed to read next pointer in loop"
                   " at %"PRIx64"\n", cur_list_entry);
            break;
        }

        while ( true )
        {
            vmi_pid_t pid = 0;
            addr_t current_process = cur_list_entry - tasks_offset;
            char *procname = NULL;
            status_t status;

            vmi_read_32_va(vmi, current_process + pid_offset, 0,
                           (uint32_t*)&pid);

            procname = vmi_read_str_va(vmi, current_process + name_offset, 0);
            if ( !procname )
            {
                syslog(LOG_CRIT, "Failed to read process name for %s",
                       target_vm_name);
                continue;
            }

            syslog(LOG_INFO, "%s [%5d] %s\n", target_vm_name, pid, procname);
            free(procname);
            procname = NULL;

            cur_list_entry = next_list_entry;
            status = vmi_read_addr_va(vmi, cur_list_entry, 0, &next_list_entry);
            if ( VMI_FAILURE == status )
            {
                syslog(LOG_CRIT, "Failed to advance through task list"
                       " for VM: %s", target_vm_name);
                break;
            }
            if ( cur_list_entry == list_head )
                break;
        }
        rc = 0;
    }
    while ( 0 );

    syslog(LOG_INFO, "%s --- end of process list\n", target_vm_name);

    return rc;
}

int
list_kernel_modules(vmi_instance_t vmi, const char *target_vm_name)
{
    addr_t next_module, list_head;

    vmi_read_addr_ksym(vmi, "modules", &next_module);
    list_head = next_module;

    while ( 1 )
    {
        addr_t tmp_next = 0;
        char *module_name = NULL;

        vmi_read_addr_va(vmi, next_module, 0, &tmp_next);

        if ( list_head == tmp_next )
            break;

        /* handle 64-bit paging: */
        if ( VMI_PM_IA32E == vmi_get_page_mode(vmi, 0) )
            module_name = vmi_read_str_va(vmi, next_module + 16, 0);
        else
            module_name = vmi_read_str_va(vmi, next_module + 8, 0);

        syslog(LOG_INFO, "%s : %s", target_vm_name, module_name);
        free(module_name);

        next_module = tmp_next;
    }

    syslog(LOG_INFO, "%s --- end of kernel module list", target_vm_name);

    return 0;
}

#define MONITOR_OP_LIST_PROCESSES       1
#define MONITOR_OP_LIST_KERNEL_MODULES  2

int monitor_action(char *target_vm_name, unsigned int op)
{
    vmi_instance_t vmi;
    int rc = -1;

    /* Using VM config data in main config file. (ie. /etc/libvmi.conf )*/
    if ( vmi_init_complete(&vmi, target_vm_name,
               VMI_INIT_DOMAINNAME, /* identify the target domain by its name */
               NULL,                      /* no additional init data required */
               VMI_CONFIG_GLOBAL_FILE_ENTRY, /* VM config is in supplied file */
               NULL,                           /* VM config not supplied here */
               NULL)                                /* no error report output */
        == VMI_FAILURE )

    {
        syslog(LOG_ERR, "Failed to init LibVMI library for VM %s",
               target_vm_name);
        return 1;
    }

    do {
        if ( VMI_OS_LINUX != vmi_get_ostype(vmi) )
        {
            syslog(LOG_ERR, "Aborting: Not a Linux VM: %s", target_vm_name);
            break;
        }
        if ( VMI_FAILURE == vmi_pause_vm(vmi) )
        {
            syslog(LOG_ERR, "Failed to pause VM %s", target_vm_name);
            break;
        }
        switch ( op )
        {
            case MONITOR_OP_LIST_PROCESSES :
                rc = list_processes(vmi, target_vm_name);
                break;
            case MONITOR_OP_LIST_KERNEL_MODULES :
                rc = list_kernel_modules(vmi, target_vm_name);
                break;
            default:
                syslog(LOG_ERR, "Unknown VMI operation");
        }

        vmi_resume_vm(vmi);

    } while ( 0 );

    vmi_destroy(vmi);

    return rc;
}

int server_socket(char *socket_name, int *p_sock)
{
    int rc = -1;
    int sock, flags;
    struct sockaddr_un server;

    do {
        sock = socket(AF_UNIX, SOCK_STREAM, 0);
        if ( sock < 0 )
        {
            syslog(LOG_ERR, "Error opening socket: %d\n", sock);
            break;
        }

        /* Set socket to non-blocking */
        flags = fcntl(sock, F_GETFL);
        if ( flags < 0 )
        {
            syslog(LOG_ERR, "Error querying socket flags: %d\n", flags);
            break;
        }
        rc = fcntl(sock, F_SETFL, flags | O_NONBLOCK );
        if ( rc < 0 )
        {
            syslog(LOG_ERR, "Error setting socket flags to: %d err: %d\n",
                    flags, rc);
            break;
        }

        memset(&server, 0, sizeof(server));
        server.sun_family = AF_UNIX;
        strcpy(server.sun_path, socket_name);

        if ( (rc = bind(sock, (struct sockaddr *)&server, sizeof(server))) )
        {
            syslog(LOG_ERR, "Error binding socket: %d\n", rc);
            break;
        }

        if ( (rc = listen(sock, LISTEN_MAX_BACKLOG)) )
        {
            syslog(LOG_ERR, "Error listening on socket: %d\n", rc);
            break;
        }
        *p_sock = sock;
        rc = 0;
    }
    while ( 0 );

    return rc;
}

void prep_command_buf(char *buf, unsigned int buf_len,
                      const char *command, unsigned int command_len)
{
    int i;
    strncpy(buf, command + command_len + 1, buf_len);
    for ( i = 0; i < buf_len; i++ )
        if ( buf[i] == '\n' ) { buf[i] = '\0'; break; }
    buf[buf_len - 1] = 0;
}

/*
 * commands for immediate action:
 *
 *  process-list <vmname>
 *  kernel-modules <vmname>
 *
 * commands for interaction with schedule:
 *
 *  schedule <command> <vmname> <timing>
 */
#define COMMAND_NOTIMPL -2
#define COMMAND_ERROR -1
#define COMMAND_OK 0
#define COMMAND_QUIT 1

int process_command(const char *command, unsigned int len)
{
    int rc = -1;
    char buf[1024];

    /* process-list <vm identifier> */
    if ( (len > 13) && strncmp(command, "process-list ", 13) == 0 )
    {
        prep_command_buf(buf, sizeof(buf), command, 12);
        syslog(LOG_INFO, "Retrieving process list for VM: %s", buf);
        rc = monitor_action(buf, MONITOR_OP_LIST_PROCESSES) ? COMMAND_ERROR
                                                            : COMMAND_OK;
    }
    else if ( (len > 15) && strncmp(command, "kernel-modules ", 15) == 0 )
    {
        prep_command_buf(buf, sizeof(buf), command, 14);
        syslog(LOG_INFO, "Retrieving kernel module list for VM: %s", buf);
        rc = monitor_action(buf, MONITOR_OP_LIST_KERNEL_MODULES)
             ? COMMAND_ERROR : COMMAND_OK;
    }
    else if ( (len > 9) && strncmp(command, "schedule ", 9) == 0 )
    {
        syslog(LOG_ERR, "scheduling not implemented yet");
        rc = COMMAND_NOTIMPL;
    }
    else if ( (len == 5) && strncmp(command, "quit\n", 5) == 0 )
    {
        syslog(LOG_ERR, "quit");
        rc = COMMAND_QUIT;
    }
    else
    {
        syslog(LOG_ERR, "unknown command received");
        rc = COMMAND_ERROR;
    }
    return rc;
}

int reply(int client_socket, const char *msg)
{
    ssize_t nbytes;

#define MAX_REPLY_STRLEN 1024

    nbytes = send(client_socket, msg, strnlen(msg, MAX_REPLY_STRLEN), 0);
    if ( nbytes < 0 )
        syslog(LOG_ERR, "error replying on connection\n");
    return nbytes;
}

static volatile sig_atomic_t looping = 1;

void interrupt_signal_handler(int _)
{
    looping = 0;
}

int main(int argc, char **argv)
{
    int sock;
    int rc = 1;
    char *filename;
    char *exe_name = "<executable name>";
    struct sigaction act;

    act.sa_handler = interrupt_signal_handler;
    sigaction(SIGINT, &act, NULL);

    if ( argc != 2 )
    {
        syslog(LOG_ERR, "Incorrect number of args: %d\n", argc);
        if ( argc > 0 )
            exe_name = argv[0];
        syslog(LOG_ERR, "Expecting: %s <socket filename>\n", exe_name);
        goto out;
    }
    filename = argv[1];
    dprintf("socket filename: %s\n", filename);

    openlog(MONITOR_LOG_IDENT,
            LOG_CONS |  /* log to system console if system logger unavailable */
            LOG_NDELAY |/* open connection immediately */
            LOG_PERROR, /* log to stderr as well */
            LOG_DAEMON);

    syslog(LOG_NOTICE, "Monitor started. uid: %d", getuid());

    if ( server_socket(filename, &sock) )
        goto out;

    /* At this point, assume that this process created the server socket file,
     * so fair to unlink it on exit.
     */

    while ( looping )
    {
        int client_socket = accept(sock, NULL, NULL);
        if (client_socket == -1)
        {
            if ( errno == EWOULDBLOCK )
            {
                /* currently no work to do here, but that will not
                 * always be the case.
                 */
                sleep(1);
            }
            else
            {
                syslog(LOG_ERR, "error when accepting connection: %d\n", errno);
                goto out;
            }
        }
        else
        {
            ssize_t nbytes;
            char buf[1024];

            dprintf("Connection established.\n");

            nbytes = recv(client_socket, buf, sizeof(buf), MSG_CMSG_CLOEXEC);
            if ( nbytes < 0 )
            {
                syslog(LOG_ERR, "error when reading from connection: %ld",
                       nbytes);
                goto out;
            }

            dprintf("read %ld bytes %s", nbytes, buf);
            switch ( process_command(buf, nbytes) )
            {
            case COMMAND_OK:
                reply(client_socket, "ack\n");
                break;
            case COMMAND_NOTIMPL:
                reply(client_socket, "nack: not implemented\n");
                break;
            case COMMAND_ERROR:
                reply(client_socket, "nack: error\n");
                break;
            case COMMAND_QUIT:
                reply(client_socket, "ack\n");
                looping = false;
                break;
            }

            close(client_socket);
        }
    }
    rc = 0;

    unlink(filename);

out:
    syslog(LOG_NOTICE, "Monitor exiting: %d", rc);
    return rc;
}
