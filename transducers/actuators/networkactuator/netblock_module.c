/*
*****************************************************************
      Netfilter Module for blocking network access              *
							        *
      Copyright (c) 2018 by Raytheon BBN Technologies Corp.     *
							        *
*****************************************************************
*/

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/netfilter_ipv6.h>
#include <linux/mutex.h>
#include <linux/spinlock.h>
#include <linux/ip.h>
#include <linux/ipv6.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/fs.h>
#include <linux/string.h>
#include "include/kmap.h"

MODULE_AUTHOR("Raytheon BBN Technologies");
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Network and Transport Layer Firewall");
MODULE_VERSION("0.1");

static DEFINE_MUTEX(netblockchar_mutex);
static DEFINE_SPINLOCK(map_spinlock);

//   Rule operations
#define UNBLOCK_OUTGOING_SRC_IPV4_IP 0
#define BLOCK_OUTGOING_SRC_IPV4_IP 1
#define UNBLOCK_INCOMING_SRC_IPV4_IP 2
#define BLOCK_INCOMING_SRC_IPV4_IP 3
#define UNBLOCK_OUTGOING_DST_IPV4_IP 4
#define BLOCK_OUTGOING_DST_IPV4_IP 5
#define UNBLOCK_INCOMING_DST_IPV4_IP 6
#define BLOCK_INCOMING_DST_IPV4_IP 7
#define UNBLOCK_OUTGOING_SRC_IPV6_IP 8
#define BLOCK_OUTGOING_SRC_IPV6_IP 9
#define UNBLOCK_INCOMING_SRC_IPV6_IP 10
#define BLOCK_INCOMING_SRC_IPV6_IP 11
#define UNBLOCK_OUTGOING_DST_IPV6_IP 12
#define BLOCK_OUTGOING_DST_IPV6_IP 13
#define UNBLOCK_INCOMING_DST_IPV6_IP 14
#define BLOCK_INCOMING_DST_IPV6_IP 15
#define UNBLOCK_OUTGOING_SRC_TCP_PORT 16
#define BLOCK_OUTGOING_SRC_TCP_PORT 17
#define UNBLOCK_INCOMING_SRC_TCP_PORT 18
#define BLOCK_INCOMING_SRC_TCP_PORT 19
#define UNBLOCK_OUTGOING_DST_TCP_PORT 20
#define BLOCK_OUTGOING_DST_TCP_PORT 21
#define UNBLOCK_INCOMING_DST_TCP_PORT 22
#define BLOCK_INCOMING_DST_TCP_PORT 23
#define UNBLOCK_OUTGOING_SRC_UDP_PORT 24
#define BLOCK_OUTGOING_SRC_UDP_PORT 25
#define UNBLOCK_INCOMING_SRC_UDP_PORT 26
#define BLOCK_INCOMING_SRC_UDP_PORT 27
#define UNBLOCK_OUTGOING_DST_UDP_PORT 28
#define BLOCK_OUTGOING_DST_UDP_PORT 29
#define UNBLOCK_INCOMING_DST_UDP_PORT 30
#define BLOCK_INCOMING_DST_UDP_PORT 31
#define UNBLOCK_OUTGOING_SRC_IP_PORT 32
#define BLOCK_OUTGOING_SRC_IP_PORT 33
#define UNBLOCK_INCOMING_SRC_IP_PORT 34
#define BLOCK_INCOMING_SRC_IP_PORT 35
#define UNBLOCK_OUTGOING_DST_IP_PORT 36
#define BLOCK_OUTGOING_DST_IP_PORT 37
#define UNBLOCK_INCOMING_DST_IP_PORT 38
#define BLOCK_INCOMING_DST_IP_PORT 39


//   Commands
#define BLOCK "block"
#define UNBLOCK "unblock"
#define INCOMING "incoming"
#define OUTGOING "outgoing"
#define SRC "src"
#define DST "dst"
#define IPV4 "ipv4"
#define IPV6 "ipv6"
#define TCP "tcp"
#define UDP "udp"
#define IPPORT "ipport"
#define RESET "reset"

//   Character Device
#define  DEVICE_NAME "netblockchar"
#define  CLASS_NAME  "netblock"


//   Variables pertaining to character device driver
//   Character Device driver used as user to kernel commununication
//   mechanism
static int majorNumber;
static char message[256] = {0};
static struct class*  netblockcharClass  = NULL;
static struct device* netblockcharDevice = NULL;

//   Prototype functions for character device driver
static int device_open(struct inode *, struct file *);
static int device_release(struct inode *, struct file *);
static ssize_t device_write(struct file *, const char *, size_t, loff_t *);

//  Prototype functions for map access
static int safe_map_set(map_int_t*, const char*);
static void safe_map_remove(map_int_t*, const char*);
static bool safe_map_check(map_int_t*, const char*);
static void safe_map_clear(map_int_t *m);

//   File Operations structure for character device driver callbacks
static struct file_operations fops = {
	.write = device_write,
	.open = device_open,
	.release = device_release,
};

//   Structure to hold packet information as we parse it
struct packet_info{
	char* src_ip;
	char* dst_ip;
	char* src_port;
	char* dst_port;
	int proto;
	bool incoming;
	bool ipv4;
};

//   Prototype functions for packet processing
unsigned int process_transport(struct sk_buff *, struct packet_info *);
unsigned int process_ip(struct sk_buff *, bool, bool);

//   netfilter hook options
static struct nf_hook_ops nfho_ipv4_in;
static struct nf_hook_ops nfho_ipv4_out;
static struct nf_hook_ops nfho_ipv6_in;
static struct nf_hook_ops nfho_ipv6_out;


struct packetRules {
	//Hashmaps for various types of firewall rules

	map_int_t src_tcp;
	map_int_t dst_tcp;
	map_int_t src_udp;
	map_int_t dst_udp;

	/*
		The below maps will hold:

		IPv4 addresses, IPv6 addresses,
		IPv4:port combos, IPv6:Port combos
	*/
	map_int_t src_ip;
	map_int_t dst_ip;
	map_int_t src_ip_port;
	map_int_t dst_ip_port;
};


//   Function for clearing an entire ruleset
static void resetRules(struct packetRules* rules){

		//remove src IP rules
		safe_map_clear(&rules->src_ip);

                //remove dst IP rules
                safe_map_clear(&rules->dst_ip);

		//remove IP srcPort combo rules
                safe_map_clear(&rules->src_ip_port);

		//remove IP dstPort combo rules
		safe_map_clear(&rules->dst_ip_port);

                //remove src TCP rules
                safe_map_clear(&rules->src_tcp);

                //remove dst TCP rules
                safe_map_clear(&rules->dst_tcp);

                //remove src UDP rules
                safe_map_clear(&rules->src_udp);

                //remove dst UDP rules
                safe_map_clear(&rules->dst_udp);
}

//   Structure for holding all the firewall rules
static struct packetRules incomingRules;
static struct packetRules outgoingRules;

//   Incoming IPv4 packets hook
unsigned int ipv4_in_hook(void* priv, struct sk_buff *skb, const struct nf_hook_state *state){
	return process_ip(skb, true, true);
}

//   Outgoing IPv4 packets hook
unsigned int ipv4_out_hook(void* priv, struct sk_buff *skb, const struct nf_hook_state *state){
	return process_ip(skb, false, true);
}

//   Incoming IPv6 packets hook
unsigned int ipv6_in_hook(void* priv, struct sk_buff *skb, const struct nf_hook_state *state){
	return process_ip(skb, true, false);
}

//   Outgoing IPv6 packets hook
unsigned int ipv6_out_hook(void* priv, struct sk_buff *skb, const struct nf_hook_state *state){
	return process_ip(skb, false, false);
}


unsigned int process_ip(struct sk_buff *skb, bool incoming, bool ipv4){

	void* ip_header;
	char ip_src[40];
	char ip_dst[40];
	char ip_version;
	struct packet_info info;
	bool val;
	int proto;

	if(!skb){
		return NF_ACCEPT;
	}

	//Grab IP header based on IP version
	//retrieve source and destination addresses for the packet
	//retreive transport protocol for the packet
	if(ipv4){
		ip_header = (struct iphdr*) ip_hdr(skb);
		if(!ip_header)
			return NF_ACCEPT;

		snprintf(ip_src, 16, "%pI4", &((struct iphdr*) ip_header)->saddr);
		snprintf(ip_dst, 16, "%pI4", &((struct iphdr*) ip_header)->daddr);
		proto = ((struct iphdr*)ip_header)->protocol;
		ip_version = '4';
	}else{
		ip_header = (struct ipv6hdr*) ipv6_hdr(skb);
		if(!ip_header)
			return NF_ACCEPT;

		snprintf(ip_src, 40, "%pI6", &((struct ipv6hdr*) ip_header)->saddr);
		snprintf(ip_dst, 40, "%pI6", &((struct ipv6hdr*) ip_header)->daddr);
		proto = ((struct ipv6hdr*)ip_header)->nexthdr;
		ip_version = '6';
	}

	info.src_ip = &ip_src[0];
	info.dst_ip = &ip_dst[0];
	info.proto = proto;
	info.incoming = incoming;
	info.ipv4 = ipv4;

	//perform ruleset lookup based on traffic direction
	if(incoming){
		val = safe_map_check(&incomingRules.src_ip, ip_src);
		if(val){
                	//drop traffic
                	printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Incoming Protocol: IPv%c src: %s dst: %s", ip_version, ip_src, ip_dst);
                	return NF_DROP;
        	}
                val = safe_map_check(&incomingRules.dst_ip, ip_dst);
                if(val){
                        //drop traffic
			printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Incoming Protocol: IP%c src: %s dst: %s", ip_version, ip_src, ip_dst);
                        return NF_DROP;
                }

	}
	else{
                val = safe_map_check(&outgoingRules.src_ip, ip_src);
                if(val){
                        //drop traffic
			printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Outgoing Protocol: IPv%c src: %s dst: %s", ip_version, ip_src, ip_dst);
                        return NF_DROP;
                }
                val = safe_map_check(&outgoingRules.dst_ip, ip_dst);
                if(val){
                        //drop traffic
                        printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Outgoing Protocol: IPv%c src: %s dst: %s", ip_version, ip_src, ip_dst);
                        return NF_DROP;
                }

	}

	return process_transport(skb, &info);

}

unsigned int process_transport(struct sk_buff* skb, struct packet_info* info){

	struct tcphdr* tcp_header;
	struct udphdr* udp_header;
	uint16_t dst_port;
	uint16_t src_port;
	char sport[6];
	char dport[6];
	char ipport_combo[46];
	bool val;

	if (info->proto == IPPROTO_TCP){

		if(info->ipv4)
			tcp_header = (struct tcphdr*)((__u32*)ip_hdr(skb) + ip_hdr(skb)->ihl);
		else
			tcp_header = (struct tcphdr*)ipipv6_hdr(skb);

		if(!tcp_header){
			return NF_ACCEPT;
		}

		dst_port = ntohs(tcp_header->dest);
		src_port = ntohs(tcp_header->source);

		snprintf(dport, 6, "%d", dst_port);
		snprintf(sport, 6, "%d", src_port);


		//Check if TCP port is permitted
		if(info->incoming){
                	val = safe_map_check(&incomingRules.src_tcp, sport);
                	if(val){
                        	//drop traffic
				printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Incoming Protocol: TCP src: %s dst: %s", sport, dport);
                        	return NF_DROP;
                	}
			val = safe_map_check(&incomingRules.dst_tcp, dport);
                        if(val){
                                //drop traffic
				printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Incoming Protocol: TCP src: %s dst: %s", sport, dport);
                                return NF_DROP;
                        }
		}else{
                        val = safe_map_check(&outgoingRules.src_tcp, sport);
                        if(val){
                                //drop traffic
                                printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Outgoing Protocol: TCP src: %s dst: %s", sport, dport);
                                return NF_DROP;
                        }
                        val = safe_map_check(&outgoingRules.dst_tcp, dport);
                        if(val){
                                //drop traffic
				printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Outgoing Protocol: TCP src: %s dst: %s", sport, dport);
                                return NF_DROP;
                        }
		}

	}else if (info->proto == IPPROTO_UDP){

		if(info->ipv4)
			udp_header = (struct udphdr*)((__u32*)ip_hdr(skb) + ip_hdr(skb)->ihl);
		else
			udp_header = (struct udphdr*)ipipv6_hdr(skb);

		if(!udp_header){
			return NF_ACCEPT;
		}

		dst_port = ntohs(udp_header->dest);
		src_port = ntohs(udp_header->source);

		snprintf(dport, 6, "%d", dst_port);
		snprintf(sport, 6, "%d", src_port);

                //Check if TCP port is permitted
                if(info->incoming){
                        val = safe_map_check(&incomingRules.src_udp, sport);
                        if(val){
                                //drop traffic
                                printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Incoming Protocol: UDP src: %s dst: %s", sport, dport);
                                return NF_DROP;
                        }
                        val = safe_map_check(&incomingRules.dst_udp, dport);
                        if(val){
                                //drop traffic
				printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Incoming Protocol: UDP src: %s dst: %s", sport, dport);
                                return NF_DROP;
                        }
                }else{
                        val = safe_map_check(&outgoingRules.src_udp, sport);
                        if(val){
                                //drop traffic
                                printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Outgoing Protocol: UDP src: %s dst: %s", sport, dport);
                                return NF_DROP;
                        }
                        val = safe_map_check(&outgoingRules.dst_udp, dport);
                        if(val){
                                //drop traffic
                                printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Outgoing Protocol: UDP src: %s dst: %s", sport, dport);
                                return NF_DROP;
                        }
                }

	}

	info->src_port = &sport[0];
	info->dst_port = &dport[0];

	//Lastly, check if IP port combo is permitted
	if(info->incoming){
		//combine IP and port
		snprintf(ipport_combo, 46, "%s:%s", info->src_ip, info->src_port);
		val = safe_map_check(&incomingRules.src_ip_port, ipport_combo);
		if(val){
			printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Incoming Protocol: IPPort src: %s srcport: %s", info->src_ip, info->src_port);
			return NF_DROP;
		}
		snprintf(ipport_combo, 46, "%s:%s", info->src_ip, info->dst_port);
		val = safe_map_check(&incomingRules.dst_ip_port, ipport_combo);
                if(val){
                        printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Incoming Protocol: IPPort src: %s dstport: %s", info->src_ip, info->dst_port);
                        return NF_DROP;
                }

	}else{
                //combine IP and port
                snprintf(ipport_combo, 46, "%s:%s", info->dst_ip, info->src_port);
                val = safe_map_check(&outgoingRules.src_ip_port, ipport_combo);
                if(val){
                        printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Outgoing Protocol: IPPort dst: %s srcport: %s", info->dst_ip, info->src_port);
                        return NF_DROP;
                }
                snprintf(ipport_combo, 46, "%s:%s", info->src_ip, info->dst_port);
                val = safe_map_check(&outgoingRules.dst_ip_port, ipport_combo);
                if(val){
                        printk(KERN_INFO "LogType: VirtueNetblock Action: Blocked Direction: Outgoing Protocol: IPPort dst: %s dstport: %s", info->dst_ip, info->dst_port);
                        return NF_DROP;
                }
	}

	return NF_ACCEPT;
}


//   Called when the module is loaded
int init_module(){

	mutex_init(&netblockchar_mutex);
	spin_lock_init(&map_spinlock);

	mutex_lock(&netblockchar_mutex);

	//Dynamically get Major number for character device driver
	majorNumber = register_chrdev(0, DEVICE_NAME, &fops);
	if (majorNumber<0){
		printk(KERN_ALERT "LogType: VirtueNetblock Action: registerCharDevice Result: Failed");
	      	return majorNumber;
	}
	printk(KERN_INFO "netblock: registered correctly with major number %d", majorNumber);

	// Register the device class
	netblockcharClass = class_create(THIS_MODULE, CLASS_NAME);
	if(IS_ERR(netblockcharClass)){
	      	unregister_chrdev(majorNumber, DEVICE_NAME);
	      	printk(KERN_ALERT "LogType: VirtueNetblock Action: registerCharDevice Result: Failed");
	      	return PTR_ERR(netblockcharClass);
	}

	// Register the device driver
	netblockcharDevice = device_create(netblockcharClass, NULL, MKDEV(majorNumber, 0), NULL, DEVICE_NAME);
	if (IS_ERR(netblockcharDevice)){
	      	class_destroy(netblockcharClass);
	      	unregister_chrdev(majorNumber, DEVICE_NAME);
	      	printk(KERN_ALERT "LogType: VirtueNetblock Action: registerCharDevice Result: Failed");
	      	return PTR_ERR(netblockcharDevice);
	}
   	printk(KERN_INFO "LogType: VirtueNetblock Action: registerCharDevice Result: Success");

        //initialize hashmaps
        map_init(&incomingRules.src_ip);
        map_init(&incomingRules.dst_ip);
        map_init(&incomingRules.src_tcp);
        map_init(&incomingRules.dst_tcp);
        map_init(&incomingRules.src_udp);
        map_init(&incomingRules.dst_udp);
        map_init(&incomingRules.src_ip_port);
	map_init(&incomingRules.dst_ip_port);

        map_init(&outgoingRules.src_ip);
        map_init(&outgoingRules.dst_ip);
        map_init(&outgoingRules.src_tcp);
        map_init(&outgoingRules.dst_tcp);
        map_init(&outgoingRules.src_udp);
        map_init(&outgoingRules.dst_udp);
        map_init(&outgoingRules.src_ip_port);
	map_init(&outgoingRules.dst_ip_port);

	mutex_unlock(&netblockchar_mutex);

	//Set up Netfilter hook
	nfho_ipv4_in.hook = ipv4_in_hook;
	nfho_ipv4_in.hooknum = NF_INET_LOCAL_IN;
	nfho_ipv4_in.pf = PF_INET;
	nfho_ipv4_in.priority = NF_IP_PRI_FIRST;
	nf_register_net_hook(&init_net, &nfho_ipv4_in);

	nfho_ipv4_out.hook = ipv4_out_hook;
	nfho_ipv4_out.hooknum = NF_INET_LOCAL_OUT;
	nfho_ipv4_out.pf = PF_INET;
	nfho_ipv4_out.priority = NF_IP_PRI_FIRST;
	nf_register_net_hook(&init_net, &nfho_ipv4_out);

	nfho_ipv6_in.hook = ipv6_in_hook;
	nfho_ipv6_in.hooknum = NF_INET_LOCAL_IN;
	nfho_ipv6_in.pf = PF_INET6;
	nfho_ipv6_in.priority = NF_IP6_PRI_FIRST;
	nf_register_net_hook(&init_net, &nfho_ipv6_in);

	nfho_ipv6_out.hook = ipv6_out_hook;
	nfho_ipv6_out.hooknum = NF_INET_LOCAL_OUT;
	nfho_ipv6_out.pf = PF_INET6;
	nfho_ipv6_out.priority = NF_IP6_PRI_FIRST;
	nf_register_net_hook(&init_net, &nfho_ipv6_out);

	printk(KERN_INFO "LogType: VirtueNetblock Action: Load Result: Success");
	return 0;
}


//   Called when the module is removed/unloaded
void cleanup_module(){

	nf_unregister_net_hook(&init_net, &nfho_ipv4_in);
        nf_unregister_net_hook(&init_net, &nfho_ipv4_out);
        nf_unregister_net_hook(&init_net, &nfho_ipv6_in);
        nf_unregister_net_hook(&init_net, &nfho_ipv6_out);

	mutex_lock(&netblockchar_mutex);

	device_destroy(netblockcharClass, MKDEV(majorNumber, 0));
   	class_unregister(netblockcharClass);
   	class_destroy(netblockcharClass);
   	unregister_chrdev(majorNumber, DEVICE_NAME);
   	printk(KERN_INFO "LogType: VirtueNetblock Action: unregisterCharDevice Result: Success");

	mutex_unlock(&netblockchar_mutex);
	mutex_destroy(&netblockchar_mutex);

	map_deinit(&incomingRules.src_ip);
        map_deinit(&incomingRules.dst_ip);
        map_deinit(&incomingRules.src_tcp);
        map_deinit(&incomingRules.dst_tcp);
        map_deinit(&incomingRules.src_udp);
        map_deinit(&incomingRules.dst_udp);
        map_deinit(&incomingRules.src_ip_port);
	map_deinit(&incomingRules.dst_ip_port);

        map_deinit(&outgoingRules.src_ip);
        map_deinit(&outgoingRules.dst_ip);
        map_deinit(&outgoingRules.src_tcp);
        map_deinit(&outgoingRules.dst_tcp);
        map_deinit(&outgoingRules.src_udp);
        map_deinit(&outgoingRules.dst_udp);
        map_deinit(&outgoingRules.src_ip_port);
	map_deinit(&outgoingRules.dst_ip_port);

	printk(KERN_INFO "LogType: VirtueNetblock Action: Unload Result: Success");

}

static int device_open(struct inode *inodep, struct file *filep){
   	mutex_lock(&netblockchar_mutex);
   	return 0;
}


static ssize_t device_write(struct file *filep, const char *buffer, size_t len, loff_t *offset){

	char* cursor;
	char* token;
	unsigned char rule;
	int count;
   	snprintf(message, 255,"%s", buffer);

	if(strcmp(message, RESET) == 0){
		//Remove all rules in the kmaps
		printk(KERN_INFO "LogType: VirtueNetblock Action: ResetRules");
		resetRules(&outgoingRules);
		resetRules(&incomingRules);
		return len;
	}

	//Parse the incoming rule
	/*
		Note that each rule is represented as a sequence of bits:

		ACTION:    1st bit:         [0=unblock, 1=block]
		DIRECTION: 2nd bit:         [0=outgoing, 1=incoming]
		SRC/DEST:  3rd bit:         [0=src, 1=dst]
		PROTOCOL:  4th,5th, 6th bit: [000=ipv4, 001=ipv6, 010=tcp, 011=udp, 100=combo]

		More bits can be added to this fourth (protocol) field to support many more
		protocols. The bit operations assume 1st bit is least significant.

		Example: 011101 = 29 ---> block outgoing dst udp
	*/
	cursor = &message[0];
	rule = 0;
	count = 0;
	while(cursor != NULL){
		count++;
		token = strsep(&cursor," ");
		if(strcmp(token, UNBLOCK) == 0){
			//do nothing... don't flip bit
		}else if(strcmp(token, BLOCK) == 0){
			rule = rule | 0x1;
		}else if(strcmp(token, OUTGOING) == 0){
			//do nothing... don't flip bit
		}else if(strcmp(token, INCOMING) == 0){
			rule = rule | 0x2;
		}else if(strcmp(token, SRC) == 0){
			//do nothing... don't flip bit
		}else if(strcmp(token, DST) == 0){
			rule = rule | 0x4;
		}else if(strcmp(token, IPV4) == 0){
			//do nothing... don't flip bit
		}else if(strcmp(token, IPV6) == 0){
			rule = rule | 0x8;
		}else if(strcmp(token, TCP) == 0){
			rule = rule | 0xC;
		}else if(strcmp(token, UDP) == 0){
			rule = rule | 0x10;
		}else if(strcmp(token, IPPORT) == 0){
			rule = rule | 0x20;
		}else{
			if(cursor != NULL){
				printk(KERN_INFO "LogType: VirtueNetblock Action: ParseCommand Result: Failed");
				return -1;
			}
		}
	}

	if(count != 5){
		printk(KERN_INFO "LogType: VirtueNetblock Action: ParseCommand Result: Failed");
		return -1;
	}

	//Apply action to ruleset
	//Note: IPv4, IPv6 use the same map
	//      IP:port for src and dst use the same map
	switch(rule){
		case UNBLOCK_OUTGOING_SRC_IPV4_IP:
		case UNBLOCK_OUTGOING_SRC_IPV6_IP:
			safe_map_remove(&outgoingRules.src_ip, token);
			break;
		case BLOCK_OUTGOING_SRC_IPV4_IP:
		case BLOCK_OUTGOING_SRC_IPV6_IP:
			safe_map_set(&outgoingRules.src_ip, token);
			break;
		case UNBLOCK_OUTGOING_DST_IPV4_IP:
                case UNBLOCK_OUTGOING_DST_IPV6_IP:
                        safe_map_remove(&outgoingRules.dst_ip, token);
                        break;
                case BLOCK_OUTGOING_DST_IPV4_IP:
                case BLOCK_OUTGOING_DST_IPV6_IP:
                        safe_map_set(&outgoingRules.dst_ip, token);
                        break;
		case UNBLOCK_INCOMING_SRC_IPV4_IP:
		case UNBLOCK_INCOMING_SRC_IPV6_IP:
			safe_map_remove(&incomingRules.src_ip, token);
			break;
		case BLOCK_INCOMING_SRC_IPV4_IP:
		case BLOCK_INCOMING_SRC_IPV6_IP:
			safe_map_set(&incomingRules.src_ip, token);
			break;
		case UNBLOCK_INCOMING_DST_IPV4_IP:
                case UNBLOCK_INCOMING_DST_IPV6_IP:
                        safe_map_remove(&incomingRules.dst_ip, token);
                        break;
                case BLOCK_INCOMING_DST_IPV4_IP:
                case BLOCK_INCOMING_DST_IPV6_IP:
                        safe_map_set(&incomingRules.dst_ip, token);
                        break;
		case UNBLOCK_OUTGOING_SRC_TCP_PORT:
			safe_map_remove(&outgoingRules.src_tcp, token);
			break;
		case BLOCK_OUTGOING_SRC_TCP_PORT:
			safe_map_set(&outgoingRules.src_tcp, token);
			break;
		case UNBLOCK_INCOMING_SRC_TCP_PORT:
			safe_map_remove(&incomingRules.src_tcp, token);
			break;
		case BLOCK_INCOMING_SRC_TCP_PORT:
			safe_map_set(&incomingRules.src_tcp, token);
			break;
		case UNBLOCK_OUTGOING_DST_TCP_PORT:
                        safe_map_remove(&outgoingRules.dst_tcp, token);
                        break;
                case BLOCK_OUTGOING_DST_TCP_PORT:
                        safe_map_set(&outgoingRules.dst_tcp, token);
                        break;
                case UNBLOCK_INCOMING_DST_TCP_PORT:
                        safe_map_remove(&incomingRules.dst_tcp, token);
                        break;
                case BLOCK_INCOMING_DST_TCP_PORT:
                        safe_map_set(&incomingRules.dst_tcp, token);
                        break;
		case UNBLOCK_OUTGOING_SRC_UDP_PORT:
			safe_map_remove(&outgoingRules.src_udp, token);
			break;
		case BLOCK_OUTGOING_SRC_UDP_PORT:
			safe_map_set(&outgoingRules.src_udp, token);
			break;
		case UNBLOCK_INCOMING_SRC_UDP_PORT:
			safe_map_remove(&incomingRules.src_udp, token);
			break;
		case BLOCK_INCOMING_SRC_UDP_PORT:
			safe_map_set(&incomingRules.src_udp, token);
			break;
		case UNBLOCK_OUTGOING_DST_UDP_PORT:
                        safe_map_remove(&outgoingRules.dst_udp, token);
                        break;
                case BLOCK_OUTGOING_DST_UDP_PORT:
                        safe_map_set(&outgoingRules.dst_udp, token);
                        break;
                case UNBLOCK_INCOMING_DST_UDP_PORT:
                        safe_map_remove(&incomingRules.dst_udp, token);
                        break;
                case BLOCK_INCOMING_DST_UDP_PORT:
                        safe_map_set(&incomingRules.dst_udp, token);
                        break;
		case UNBLOCK_OUTGOING_SRC_IP_PORT:
			safe_map_remove(&outgoingRules.src_ip_port, token);
			break;
		case UNBLOCK_OUTGOING_DST_IP_PORT:
			safe_map_remove(&outgoingRules.dst_ip_port, token);
			break;
		case BLOCK_OUTGOING_SRC_IP_PORT:
			safe_map_set(&outgoingRules.src_ip_port, token);
			break;
                case BLOCK_OUTGOING_DST_IP_PORT:
                        safe_map_set(&outgoingRules.dst_ip_port, token);
                        break;
		case UNBLOCK_INCOMING_SRC_IP_PORT:
			safe_map_remove(&incomingRules.src_ip_port, token);
			break;
                case UNBLOCK_INCOMING_DST_IP_PORT:
                        safe_map_remove(&incomingRules.dst_ip_port, token);
                        break;
		case BLOCK_INCOMING_SRC_IP_PORT:
			safe_map_set(&incomingRules.src_ip_port, token);
			break;
                case BLOCK_INCOMING_DST_IP_PORT:
                        safe_map_set(&incomingRules.dst_ip_port, token);
                        break;
		default:
			printk(KERN_INFO "LogType: VirtueNetblock Action: ParseCommand Result: Failed");
			return -1;
	}

	printk(KERN_INFO "LogType: VirtueNetblock Action: ParseCommand Result: Success");

   	return len;
}

static int safe_map_set(map_int_t* m, const char* key){
	int ret;
	unsigned long flags;

	spin_lock_irqsave(&map_spinlock, flags);
	ret = map_set(m, key, 0);
	spin_unlock_irqrestore(&map_spinlock, flags);
	return ret;
}

static void safe_map_remove(map_int_t *m, const char* key){
	unsigned long flags;

	spin_lock_irqsave(&map_spinlock, flags);
	map_remove(m, key);
	spin_unlock_irqrestore(&map_spinlock, flags);
}

static void safe_map_clear(map_int_t *m){
	map_iter_t iter;
	const char* key;
	unsigned long flags;

	spin_lock_irqsave(&map_spinlock, flags);
        iter = map_iter(m);
        while ((key = map_next(m, &iter))) {
		map_remove(m, key);
        }
	spin_unlock_irqrestore(&map_spinlock, flags);
}

static bool safe_map_check(map_int_t *m, const char* key){
	int *val;
	bool found;
	unsigned long flags;
	found = false;

	spin_lock_irqsave(&map_spinlock, flags);
	val = map_get(m, key);
	if(val != NULL){
		found = true;
		*val = *val + 1;
	}
	spin_unlock_irqrestore(&map_spinlock, flags);
	return found;
}

static int device_release(struct inode *inodep, struct file *filep){
   	mutex_unlock(&netblockchar_mutex);
   	return 0;
}
