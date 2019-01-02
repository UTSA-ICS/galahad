/*
 * VM monitor daemon
 * Copyright (c) Star Lab Corp. 2018.
 * All rights reserved.
 *
 * Author: Christopher Clark, Oct-Dec 2018
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
#include <openssl/sha.h>

#define dprintf printf
#define PAGE_SIZE 1 << 12

/* max length of pending connections: */
#define LISTEN_MAX_BACKLOG  8

#define MONITOR_LOG_IDENT   "VMmonitor"

/*
 *-----------------------------------------------------------------------------
 * (approximate) Linux kernel data structures
 */

struct list_head {
        struct list_head *next, *prev;
};

struct security_hook_list {
    struct list_head        list;
    struct list_head        *head;

    /*union security_list_options hook;*/
    int (*hook)(struct list_head *bar);

    char                *lsm;
    int             lsm_index;
};

#define CONFIG_SECURITY_PATH
#define CONFIG_SECURITY_NETWORK
#undef CONFIG_SECURITY_INFINIBAND
#undef CONFIG_SECURITY_NETWORK_XFRM
#undef CONFIG_KEYS
#undef CONFIG_AUDIT

struct security_hook_heads {
    struct list_head binder_set_context_mgr;
    struct list_head binder_transaction;
    struct list_head binder_transfer_binder;
    struct list_head binder_transfer_file;
    struct list_head ptrace_access_check;
    struct list_head ptrace_traceme;
    struct list_head capget;
    struct list_head capset;
    struct list_head capable;
    struct list_head quotactl;
    struct list_head quota_on;
    struct list_head syslog;
    struct list_head settime;
    struct list_head vm_enough_memory;
    struct list_head bprm_set_creds;
    struct list_head bprm_check_security;
    struct list_head bprm_secureexec;
    struct list_head bprm_committing_creds;
    struct list_head bprm_committed_creds;
    struct list_head sb_alloc_security;
    struct list_head sb_free_security;
    struct list_head sb_copy_data;
    struct list_head sb_remount;
    struct list_head sb_kern_mount;
    struct list_head sb_show_options;
    struct list_head sb_statfs;
    struct list_head sb_mount;
    struct list_head sb_umount;
    struct list_head sb_pivotroot;
    struct list_head sb_set_mnt_opts;
    struct list_head sb_clone_mnt_opts;
    struct list_head sb_parse_opts_str;
    struct list_head dentry_init_security;
    struct list_head dentry_create_files_as;
#ifdef CONFIG_SECURITY_PATH
    struct list_head path_unlink;
    struct list_head path_mkdir;
    struct list_head path_rmdir;
    struct list_head path_mknod;
    struct list_head path_truncate;
    struct list_head path_symlink;
    struct list_head path_link;
    struct list_head path_rename;
    struct list_head path_chmod;
    struct list_head path_chown;
    struct list_head path_chroot;
#endif
    struct list_head inode_alloc_security;
    struct list_head inode_free_security;
    struct list_head inode_init_security;
    struct list_head inode_create;
    struct list_head inode_link;
    struct list_head inode_unlink;
    struct list_head inode_symlink;
    struct list_head inode_mkdir;
    struct list_head inode_rmdir;
    struct list_head inode_mknod;
    struct list_head inode_rename;
    struct list_head inode_readlink;
    struct list_head inode_follow_link;
    struct list_head inode_permission;
    struct list_head inode_setattr;
    struct list_head inode_getattr;
    struct list_head inode_setxattr;
    struct list_head inode_post_setxattr;
    struct list_head inode_getxattr;
    struct list_head inode_listxattr;
    struct list_head inode_removexattr;
    struct list_head inode_need_killpriv;
    struct list_head inode_killpriv;
    struct list_head inode_getsecurity;
    struct list_head inode_setsecurity;
    struct list_head inode_listsecurity;
    struct list_head inode_getsecid;
    struct list_head inode_copy_up;
    struct list_head inode_copy_up_xattr;
    struct list_head file_permission;
    struct list_head file_alloc_security;
    struct list_head file_free_security;
    struct list_head file_ioctl;
    struct list_head mmap_addr;
    struct list_head mmap_file;
    struct list_head file_mprotect;
    struct list_head file_lock;
    struct list_head file_fcntl;
    struct list_head file_set_fowner;
    struct list_head file_send_sigiotask;
    struct list_head file_receive;
    struct list_head file_open;
    struct list_head task_create;
    struct list_head task_alloc;
    struct list_head task_free;
    struct list_head cred_alloc_blank;
    struct list_head cred_free;
    struct list_head cred_prepare;
    struct list_head cred_transfer;
    struct list_head kernel_act_as;
    struct list_head kernel_create_files_as;
    struct list_head kernel_read_file;
    struct list_head kernel_post_read_file;
    struct list_head kernel_module_request;
    struct list_head task_fix_setuid;
    struct list_head task_setpgid;
    struct list_head task_getpgid;
    struct list_head task_getsid;
    struct list_head task_getsecid;
    struct list_head task_setnice;
    struct list_head task_setioprio;
    struct list_head task_getioprio;
    struct list_head task_prlimit;
    struct list_head task_setrlimit;
    struct list_head task_setscheduler;
    struct list_head task_getscheduler;
    struct list_head task_movememory;
    struct list_head task_kill;
    struct list_head task_prctl;
    struct list_head task_to_inode;
    struct list_head ipc_permission;
    struct list_head ipc_getsecid;
    struct list_head msg_msg_alloc_security;
    struct list_head msg_msg_free_security;
    struct list_head msg_queue_alloc_security;
    struct list_head msg_queue_free_security;
    struct list_head msg_queue_associate;
    struct list_head msg_queue_msgctl;
    struct list_head msg_queue_msgsnd;
    struct list_head msg_queue_msgrcv;
    struct list_head shm_alloc_security;
    struct list_head shm_free_security;
    struct list_head shm_associate;
    struct list_head shm_shmctl;
    struct list_head shm_shmat;
    struct list_head sem_alloc_security;
    struct list_head sem_free_security;
    struct list_head sem_associate;
    struct list_head sem_semctl;
    struct list_head sem_semop;
    struct list_head netlink_send;
    struct list_head d_instantiate;
    struct list_head getprocattr;
    struct list_head setprocattr;
    struct list_head ismaclabel;
    struct list_head secid_to_secctx;
    struct list_head secctx_to_secid;
    struct list_head release_secctx;
    struct list_head inode_invalidate_secctx;
    struct list_head inode_notifysecctx;
    struct list_head inode_setsecctx;
    struct list_head inode_getsecctx;
#ifdef CONFIG_SECURITY_NETWORK
    struct list_head unix_stream_connect;
    struct list_head unix_may_send;
    struct list_head socket_create;
    struct list_head socket_post_create;
    struct list_head socket_bind;
    struct list_head socket_connect;
    struct list_head socket_listen;
    struct list_head socket_accept;
    struct list_head socket_sendmsg;
    struct list_head socket_recvmsg;
    struct list_head socket_getsockname;
    struct list_head socket_getpeername;
    struct list_head socket_getsockopt;
    struct list_head socket_setsockopt;
    struct list_head socket_shutdown;
    struct list_head socket_sock_rcv_skb;
    struct list_head socket_getpeersec_stream;
    struct list_head socket_getpeersec_dgram;
    struct list_head sk_alloc_security;
    struct list_head sk_free_security;
    struct list_head sk_clone_security;
    struct list_head sk_getsecid;
    struct list_head sock_graft;
    struct list_head inet_conn_request;
    struct list_head inet_csk_clone;
    struct list_head inet_conn_established;
    struct list_head secmark_relabel_packet;
    struct list_head secmark_refcount_inc;
    struct list_head secmark_refcount_dec;
    struct list_head req_classify_flow;
    struct list_head tun_dev_alloc_security;
    struct list_head tun_dev_free_security;
    struct list_head tun_dev_create;
    struct list_head tun_dev_attach_queue;
    struct list_head tun_dev_attach;
    struct list_head tun_dev_open;
#endif  /* CONFIG_SECURITY_NETWORK */
#ifdef CONFIG_SECURITY_INFINIBAND
    struct list_head ib_pkey_access;
    struct list_head ib_endport_manage_subnet;
    struct list_head ib_alloc_security;
    struct list_head ib_free_security;
#endif  /* CONFIG_SECURITY_INFINIBAND */
#ifdef CONFIG_SECURITY_NETWORK_XFRM
    struct list_head xfrm_policy_alloc_security;
    struct list_head xfrm_policy_clone_security;
    struct list_head xfrm_policy_free_security;
    struct list_head xfrm_policy_delete_security;
    struct list_head xfrm_state_alloc;
    struct list_head xfrm_state_alloc_acquire;
    struct list_head xfrm_state_free_security;
    struct list_head xfrm_state_delete_security;
    struct list_head xfrm_policy_lookup;
    struct list_head xfrm_state_pol_flow_match;
    struct list_head xfrm_decode_session;
#endif  /* CONFIG_SECURITY_NETWORK_XFRM */
#ifdef CONFIG_KEYS
    struct list_head key_alloc;
    struct list_head key_free;
    struct list_head key_permission;
    struct list_head key_getsecurity;
#endif  /* CONFIG_KEYS */
#ifdef CONFIG_AUDIT
    struct list_head audit_rule_init;
    struct list_head audit_rule_known;
    struct list_head audit_rule_match;
    struct list_head audit_rule_free;
#endif /* CONFIG_AUDIT */
} __randomize_layout;

/*
--------------------------------------------------------------------------------
*/


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

int
validate_hook_heads(vmi_instance_t vmi, const char *vm_name,
                    const char *hook_name, unsigned char *memory,
                    addr_t *p_list_head)
{
    bool found_hook = false;
    addr_t expected_hook;
    int rc;
	size_t bytes_read;
	int loop_counter;

    rc = vmi_translate_ksym2v(vmi, hook_name, &expected_hook);
    if ( VMI_FAILURE == rc )
    {
        syslog(LOG_ERR,
               "%s ERROR failed to get addr for %s.\n",
               vm_name, hook_name);
        goto out;
    }

    /* There are 206 defined hooks at the time of writing -- again, this
     * fits within a single page of memory.
     */
    rc = vmi_read_ksym(vmi, "security_hook_heads", PAGE_SIZE, memory, NULL);
    if ( VMI_FAILURE == rc ) {
        syslog(LOG_ERR, "%s ERROR failed to read security_hook_heads memory.\n",
               vm_name);
        goto out;
    }
    /* vmi_print_hex(memory, PAGE_SIZE); */

    /* scan these lists looking for the virtue hooks as installed */
    loop_counter = 0;
    {
        struct security_hook_list *s_h_l;
        addr_t list_head = *p_list_head;
        addr_t cur_list_entry = list_head;

        while ( 1 )
        {
            rc = vmi_read_va(vmi, cur_list_entry, 0,
                             sizeof(struct security_hook_list),
                             memory, &bytes_read);
            if ( VMI_FAILURE == rc )
            {
                syslog(LOG_ERR, "%s ERROR failed to read %s list.\n",
                       vm_name, hook_name);
                goto out;
            }
            s_h_l = (struct security_hook_list *)memory;

            if ( (addr_t)(s_h_l->hook) == expected_hook )
            {
                syslog(LOG_INFO, "%s OK %s active at: %lx", vm_name, hook_name,
                    (unsigned long)s_h_l->hook);
                found_hook = true;
                break;
            }

            cur_list_entry = (addr_t)(s_h_l->list.next);

            if ( list_head == cur_list_entry )
                break;

#define MAX_LOOP_THRESHOLD 100
            if ( ++loop_counter > MAX_LOOP_THRESHOLD )
            {
                syslog(LOG_CRIT, "%s THREAT insane security hook list.\n",
                       vm_name);
                goto out;
            }
        }
    }

    if ( !found_hook )
        syslog(LOG_CRIT, "%s THREAT missing LSM security hook.\n", vm_name);

 out:
    return found_hook ? 0 : -1;
}

int
validate_hook(vmi_instance_t vmi, const char *vm_name,
              struct security_hook_list *sec_hook_list,
              unsigned int sec_hook_index,
              const char *hook_name)
{
    status_t rc;
    addr_t expected_hook;
    int ret = -1;

    rc = vmi_translate_ksym2v(vmi, hook_name, &expected_hook);
    if ( VMI_FAILURE == rc )
    {
        syslog(LOG_ERR,
               "%s ERROR failed to get addr for %s.\n",
               vm_name, hook_name);
        goto out;
    }
    syslog(LOG_INFO, "%s OK %s present at: %lx", vm_name, hook_name, expected_hook);

    if ( (addr_t)(sec_hook_list[sec_hook_index].hook) != expected_hook )
    {
        /* BAD */
        syslog(LOG_CRIT, "%s THREAT %s is COMPROMIZED. (%lx != expected %lx)\n",
               vm_name, hook_name,
               (addr_t)(sec_hook_list[sec_hook_index].hook),
               expected_hook);
        goto out;
    }
    ret = 0;

 out:
    return ret;
}

void
generate_page_hash(unsigned char *memory, char *out_digest)
{
    size_t index;
    unsigned char digest[SHA256_DIGEST_LENGTH];

    SHA256_CTX ctx;
    SHA256_Init(&ctx);

    SHA256_Update(&ctx, memory, PAGE_SIZE);

    SHA256_Final(digest, &ctx);

    for ( index = 0; index < SHA256_DIGEST_LENGTH; ++index )
        sprintf(out_digest + (2 * index), "%02x", digest[index]);
}

int
validate_hook_code(vmi_instance_t vmi, const char *vm_name,
                   const char *hook_name, unsigned char *memory)
{
    status_t rc;
    addr_t hook;
    int ret = -1;
    char human_readable_digest[SHA256_DIGEST_LENGTH * 2];

    rc = vmi_translate_ksym2v(vmi, hook_name, &hook);
    if ( VMI_FAILURE == rc )
    {
        syslog(LOG_ERR,
               "%s ERROR failed to get addr for %s.\n",
               vm_name, hook_name);
        goto out;
    }

    /*
     * It would be possible to extract the exact size of the code that
     * implements the hook from the System.map file since it is sorted
     * by address, and differencing adjacent lines should give a viable result.
     * An inspection determined that the current implementations are all
     * less than PAGE_SIZE, so hashing that fixed size works for what we need.
     */
    rc = vmi_read_ksym(vmi, hook_name, PAGE_SIZE, memory, NULL);
    if ( VMI_FAILURE == rc )
    {
        syslog(LOG_CRIT, "%s ERROR failed to read %s hook code memory.\n",
               vm_name, hook_name);
        goto out;
    }

    generate_page_hash(memory, human_readable_digest);
    syslog(LOG_INFO, "%s Digest of %s hook code: %s.\n",
           vm_name, hook_name, human_readable_digest);

    ret = 0;

 out:
    return ret;
}

int
inspect_virtue_lsm(vmi_instance_t vmi, const char *vm_name)
{
    int ret = -1;
    status_t rc;
	unsigned char *memory;
    struct security_hook_list *sec_hook_list;

    syslog(LOG_INFO, "%s --- start virtue LSM inspection", vm_name);

    /* 1. Does the virtue_hooks array contain the expected elements? */

    /* We only have six hooks: will easily fit within a single page */
    memory = malloc(PAGE_SIZE);

    rc = vmi_read_ksym(vmi, "virtue_hooks", PAGE_SIZE, memory, NULL);
    if ( VMI_FAILURE == rc ) {
        syslog(LOG_CRIT, "%s THREAT failed to read virtue_hooks memory.\n",
               vm_name);
        goto out;
    }
    /* vmi_print_hex(memory, PAGE_SIZE); */

    /* Validate the Virtue hook table */
    sec_hook_list = (struct security_hook_list*)memory;

    rc += validate_hook(vmi, vm_name, sec_hook_list, 0, "virtue_task_create") +
         validate_hook(vmi, vm_name, sec_hook_list, 1, "virtue_path_mkdir") +
         validate_hook(vmi, vm_name, sec_hook_list, 2, "virtue_socket_bind") +
         validate_hook(vmi, vm_name, sec_hook_list, 3, "virtue_socket_connect") +
         validate_hook(vmi, vm_name, sec_hook_list, 4, "virtue_inode_create") +
         validate_hook(vmi, vm_name, sec_hook_list, 5, "virtue_bprm_set_creds");

    /* 2. Are the virtue hooks installed in the security hooks? */

    syslog(LOG_INFO, "%s Validating hook heads table", vm_name);

    rc += validate_hook_heads(vmi, vm_name, "virtue_task_create", memory,
        (addr_t *)(&(((struct security_hook_heads*)memory)->task_create.next)))
       +
         validate_hook_heads(vmi, vm_name, "virtue_path_mkdir", memory,
        (addr_t *)(&(((struct security_hook_heads*)memory)->path_mkdir.next)))
       +
         validate_hook_heads(vmi, vm_name, "virtue_socket_bind", memory,
        (addr_t *)(&(((struct security_hook_heads*)memory)->socket_bind.next)))
       +
         validate_hook_heads(vmi, vm_name, "virtue_socket_connect", memory,
        (addr_t *)(&(((struct security_hook_heads*)memory)->socket_connect.next)))
       +
         validate_hook_heads(vmi, vm_name, "virtue_inode_create", memory,
        (addr_t *)(&(((struct security_hook_heads*)memory)->inode_create.next)))
       +
         validate_hook_heads(vmi, vm_name, "virtue_bprm_set_creds", memory,
        (addr_t *)(&(((struct security_hook_heads*)memory)->bprm_set_creds.next)));

    if ( rc == 0 )
    {
        syslog(LOG_INFO, "%s --- LSM inspection, hooks present: PASS", vm_name);
        ret = 0;
    }

    syslog(LOG_INFO, "%s --- Producing hook code digests", vm_name);

    /* 3. Checksum the code that implements the hooks. */
    rc += validate_hook_code(vmi, vm_name, "virtue_task_create", memory)
        +
          validate_hook_code(vmi, vm_name, "virtue_path_mkdir", memory)
        +
          validate_hook_code(vmi, vm_name, "virtue_socket_bind", memory)
        +
          validate_hook_code(vmi, vm_name, "virtue_socket_connect", memory)
        +
          validate_hook_code(vmi, vm_name, "virtue_inode_create", memory)
        +
          validate_hook_code(vmi, vm_name, "virtue_bprm_set_creds", memory);

 out:
	if ( memory )
		free(memory);

    syslog(LOG_INFO, "%s --- end of virtue LSM inspection", vm_name);
    return ret;
}

#define MONITOR_OP_LIST_PROCESSES       1
#define MONITOR_OP_LIST_KERNEL_MODULES  2
#define MONITOR_OP_INSPECT_VIRTUE_LSM   3

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
            case MONITOR_OP_INSPECT_VIRTUE_LSM :
                rc = inspect_virtue_lsm(vmi, target_vm_name);
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
    else if ( (len > 19) && strncmp(command, "inspect-virtue-lsm ", 19) == 0 )
    {
        prep_command_buf(buf, sizeof(buf), command, 18);
        syslog(LOG_INFO, "Inspecting Virtue LSM for VM: %s", buf);
        rc = monitor_action(buf, MONITOR_OP_INSPECT_VIRTUE_LSM)
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
